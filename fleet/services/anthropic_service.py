import os
import json
from langchain_anthropic import ChatAnthropic
from langchain.prompts import ChatPromptTemplate
from .rag_processor import RAGProcessor


class AnthropicService:
    def __init__(self):
        # Model 1: Szybki, do analizy TCO na podstawie Twoich danych (RAG)
        self.tco_model = ChatAnthropic(
            model="claude-opus-4-20250514",
            api_key=os.getenv("ANTHROPIC_API_KEY"),
            max_tokens=4096
        )
        # Model 2: Potężny, do analizy awaryjności na podstawie wiedzy ogólnej
        self.failure_analysis_model = ChatAnthropic(
            model="claude-opus-4-20250514",
            api_key=os.getenv("ANTHROPIC_API_KEY"),
            max_tokens=8192
        )
        # Model 3: "Dyrektor floty", do ostatecznego podsumowania
        self.summary_model = ChatAnthropic(
            model="claude-opus-4-20250514",
            api_key=os.getenv("ANTHROPIC_API_KEY"),
            max_tokens=4096
        )
        self.rag_processor = RAGProcessor()

    def _get_tco_analysis(self, criteria: dict) -> str:
        """
        Prywatna metoda do generowania analizy TCO.
        Zwraca string w formacie JSON zawierający raport HTML i listę rekomendowanych aut.
        """
        car_classes_str = ", ".join(criteria['car_class'])
        fuel_types_str = ", ".join(criteria['fuel_type'])
        search_query = (
            f"Klasy: {car_classes_str}, "
            f"Paliwo: {fuel_types_str}, "
            f"Wyposażenie: {', '.join(criteria['equipment'])}, "
            f"Cena zakupu do: {criteria['price_new']}"
        )

        context = self.rag_processor.find_relevant_context(search_query, k=20)  # Zwiększono kontekst do 20
        if not context:
            return json.dumps(
                {"html_report": "<p>Nie udało się znaleźć pasujących informacji w bazie danych do analizy TCO.</p>",
                 "recommended_cars": []})

        prompt_template = ChatPromptTemplate.from_template(
            """
            Jesteś analitykiem flotowym. Twoja odpowiedź MUSI być poprawnym obiektem JSON. Nie dołączaj żadnych wyjaśnień poza JSONem.
            Struktura JSON:
            {{
                "html_report": "...",
                "recommended_cars": ["pełna nazwa auta 1", "pełna nazwa auta 2", "itd..."]
            }}

            W kluczu "html_report" umieść kod HTML z analizą TCO.
            W kluczu "recommended_cars" umieść listę PEŁNYCH NAZW **wszystkich** modeli, które przedstawiasz w raporcie HTML (zarówno rekomendację, jak i alternatywy). Ich liczba musi się zgadzać.

            KONTEKST Z BAZY DANYCH:
            ---
            {context}
            ---

            KRYTERIA OD MENEDŻERA:
            - Klasy: {car_class} (najważniejsze)
            - Paliwo: {fuel_type} (najważniejsze)
            - Cena do: {price_new} PLN
            - Wyposażenie: {equipment}
            - Okres eksploatacji: {exploitation_period} lat
            - Przebieg: {max_mileage} km
            - Koszt przeglądu: {service_cost} PLN
            - Ceny paliw: Benzyna={petrol_price}, Diesel={diesel_price}, Prąd={electricity_price}

            ZADANIE:
            1. Znajdź w kontekście WSZYSTKIE samochody (do 5) spełniające najważniejsze kryteria (klasa, paliwo).
            2. Dla każdego z nich oblicz TCO (Utrata Wartości + Koszt Paliwa + Koszt Serwisu), bazując na danych z kontekstu.
            3. Utratę Wartości wylicz biorąc w pierwszej kolejności do wyliczeń wartości rezydualne po określonej liczbie lat, są w kontekście, jeśli ich nie znajdziesz - aproksymuj dla średniej z danego segmentu samochodów.
            4. Wypełnij szablon HTML wynikami. Pokaż 1 auto jako główną rekomendację (najniższe TCO) i resztę jako alternatywy.
            4. **Krytycznie ważne:** Zidentyfikuj WSZYSTKIE analizowane modele i umieść ich pełne nazwy w liście JSON `recommended_cars`. Jeśli w raporcie HTML są 4 samochody, na liście muszą być 4 nazwy.

            SZABLON HTML:
            <div class="analysis-container">
                <div class="card recommendation-card">
                    <div class="card-header"><span class="badge">Rekomendacja TCO</span><h3>[Nazwa polecanego samochodu]</h3></div>
                    <div class="card-body">
                        <p>[Uzasadnienie wyboru pod kątem TCO.]</p>
                        <table class="tco-table">
                            <thead><tr><th>Składnik TCO</th><th>Obliczenia</th><th>Koszt</th></tr></thead>
                            <tbody>
                                <tr><td>Utrata Wartości</td><td>[np. 150000 PLN - 75000 PLN]</td><td>[np. 75000 PLN]</td></tr>
                                <tr><td>Koszt Paliwa</td><td>[np. (100000km / 100) * 5.5l * 6.00 PLN]</td><td>[np. 33000 PLN]</td></tr>
                                <tr><td>Koszt Serwisu</td><td>[np. (100000km / 30000km) * 1200 PLN]</td><td>[np. 3600 PLN]</td></tr>
                            </tbody>
                            <tfoot><tr><td colspan="2">Całkowity Koszt Posiadania (TCO)</td><td><strong>[np. 111600 PLN]</strong></td></tr></tfoot>
                        </table>
                    </div>
                </div>
                <h4>Rozważane alternatywy (TCO)</h4>
                <div class="alternatives-grid">
                    <div class="card alternative-card">
                        <div class="card-header"><h5>[Nazwa alternatywy 1]</h5></div>
                        <div class="card-body"><p>[Krótkie uzasadnienie]</p><p><strong>Szacowane TCO: [Koszt]</strong></p></div>
                    </div>
                    <!-- Powtórz dla wszystkich innych alternatyw -->
                </div>
            </div>
            """
        )
        chain = prompt_template | self.tco_model
        response = chain.invoke({
            "context": context, "car_class": car_classes_str, "fuel_type": fuel_types_str,
            "equipment": ", ".join(criteria['equipment']) if criteria['equipment'] else "brak",
            "price_new": criteria['price_new'], "exploitation_period": criteria['exploitation_period'],
            "max_mileage": criteria['max_mileage'], "service_cost": criteria['service_cost'],
            "petrol_price": criteria['petrol_price'], "diesel_price": criteria['diesel_price'],
            "electricity_price": criteria['electricity_price'],
        })
        return response.content

    def _get_failure_analysis(self, car_name: str) -> str:
        """
        Prywatna metoda do generowania analizy awaryjności dla danego modelu.
        """
        prompt_template = ChatPromptTemplate.from_template(
            """
            Jesteś ekspertem mechaniki samochodowej. Twoim zadaniem jest analiza potencjalnych awarii i kosztów utrzymania dla konkretnego modelu samochodu. Twoja odpowiedź MUSI być kodem HTML.

            Model do analizy: **{car_name}**

            ZADANIE:
            Na podstawie swojej ogólnej wiedzy, stwórz raport w formacie HTML, który zawiera:
            1.  **Najczęstsze Usterki:** Wypunktuj 3-5 typowych problemów dla tego modelu i generacji.
            2.  **Akcje Serwisowe i Przywoławcze:** Wspomnij, czy ten model był objęty znaczącymi akcjami przywoławczymi.
            3.  **Opinia Ogólna:** Krótkie podsumowanie dotyczące niezawodności.

            Użyj poniższej struktury HTML:
            <div class="card failure-card">
                <div class="card-header">
                     <span class="badge-failure">Analiza Awaryjności</span>
                     <h3>{car_name}</h3>
                </div>
                <div class="card-body">
                    <h4>Najczęstsze Usterki:</h4>
                    <ul><li>[Opis usterki 1]</li><li>[Opis usterki 2]</li><li>[Opis usterki 3]</li></ul>
                    <h4>Akcje Serwisowe:</h4>
                    <p>[Informacje o akcjach serwisowych lub ich braku.]</p>
                    <h4>Podsumowanie Niezawodności:</h4>
                    <p>[Ogólna opinia o modelu.]</p>
                </div>
            </div>
            """
        )
        chain = prompt_template | self.failure_analysis_model
        response = chain.invoke({"car_name": car_name})
        return response.content

    def _get_final_summary(self, tco_report: str, failure_reports: str) -> str:
        """
        Prywatna metoda generująca ostateczne podsumowanie i werdykt.
        """
        prompt_template = ChatPromptTemplate.from_template(
            """
            Jesteś doświadczonym dyrektorem floty. Twoim zadaniem jest sformułowanie ostatecznego werdyktu na podstawie dwóch dostarczonych analiz: analizy kosztów (TCO) i analizy awaryjności. Twoja odpowiedź MUSI być kodem HTML.

            **ANALIZA KOSZTÓW (TCO):**
            ---
            {tco_report}
            ---

            **ANALIZA AWARYJNOŚCI:**
            ---
            {failure_reports}
            ---

            **ZADANIE:**
            1.  **Zważ oba czynniki:** Koszt i ryzyko awarii.
            2.  **Sformułuj ostateczną rekomendację:** Wskaż, który samochód jest najbardziej optymalnym wyborem, biorąc pod uwagę zarówno niskie koszty, jak i akceptowalny poziom niezawodności.
            3.  **Uzasadnij swój wybór:** Wyjaśnij, dlaczego rekomendowany model jest lepszy od pozostałych. Może się zdarzyć, że model z najniższym TCO ma wysokie ryzyko drogich awarii, co czyni go nieoptymalnym. Musisz to zauważyć i skomentować.

            Użyj poniższej struktury, aby wyróżnić ostateczny werdykt.
            <hr>
            <div class="final-verdict-container">
                <div class="verdict-header">
                    <svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="crown-icon"><path d="m2 6 3 12h14l3-12-6 7-4-7-4 7-6-7Z"/></svg>
                    <h3 class="verdict-title">Ostateczny Werdykt</h3>
                </div>
                <div class="card summary-card">
                    <div class="card-body">
                        <p class="summary-text">[Tutaj umieść swoje szczegółowe podsumowanie i uzasadnienie ostatecznego wyboru, ważąc koszty TCO i ryzyko awarii.]</p>
                        <div class="winner-announcement">
                            <p class="winner-title">Rekomendacja Optymalnego Wyboru:</p>
                            <p class="winner-car-name">[Pełna nazwa optymalnego samochodu]</p>
                        </div>
                    </div>
                </div>
            </div>
            """
        )
        chain = prompt_template | self.summary_model
        response = chain.invoke({
            "tco_report": tco_report,
            "failure_reports": failure_reports
        })
        return response.content

    def get_car_recommendation(self, criteria: dict) -> str:
        """
        Główna metoda, która orkiestruje cały proces: TCO -> Awaryjność -> Podsumowanie.
        """
        # Etap 1: Uzyskaj analizę TCO i listę aut
        tco_response_str = ""
        try:
            tco_response_str = self._get_tco_analysis(criteria)
            cleaned_json_str = tco_response_str.strip().removeprefix("```json").removesuffix("```").strip()
            tco_data = json.loads(cleaned_json_str)
            tco_html_report = tco_data.get("html_report", "<p>Błąd w raporcie HTML analizy TCO.</p>")
            recommended_cars = tco_data.get("recommended_cars", [])
        except (json.JSONDecodeError, KeyError) as e:
            print(f"Błąd przetwarzania odpowiedzi TCO: {e}")
            return f"<p>Wystąpił błąd podczas analizy TCO. Otrzymano nieprawidłowy format JSON.</p><pre>{tco_response_str}</pre>"

        if not recommended_cars:
            return tco_html_report

        # Etap 2: Dla każdego polecanego auta, uzyskaj analizę awaryjności
        failure_reports_html = ""
        for car in recommended_cars:
            try:
                failure_report = self._get_failure_analysis(car)
                failure_reports_html += failure_report
            except Exception as e:
                print(f"Błąd podczas analizy awaryjności dla {car}: {e}")
                failure_reports_html += f"<p>Nie udało się przeprowadzić analizy awaryjności dla {car}.</p>"

        # Etap 3: Uzyskaj ostateczne podsumowanie
        final_summary_html = ""
        try:
            summary_tco_context = tco_html_report
            final_summary_html = self._get_final_summary(summary_tco_context, failure_reports_html)
        except Exception as e:
            print(f"Błąd podczas generowania ostatecznego podsumowania: {e}")
            final_summary_html = "<p>Nie udało się wygenerować ostatecznego podsumowania.</p>"

        # Etap 4: Połącz wszystkie raporty w jedną odpowiedź HTML
        final_html_report = tco_html_report + "<hr><h3>Analiza Awaryjności i Niezawodności</h3>" + failure_reports_html + final_summary_html
        return final_html_report
