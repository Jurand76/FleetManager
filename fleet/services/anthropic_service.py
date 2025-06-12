import os
from langchain_anthropic import ChatAnthropic
from langchain.prompts import ChatPromptTemplate
from .rag_processor import RAGProcessor


class AnthropicService:
    def __init__(self):
        self.rag_processor = RAGProcessor()
        self.chat_model = ChatAnthropic(
            model="claude-opus-4-20250514",  # Możesz wybrać inny model, np. Haiku
            api_key=os.getenv("ANTHROPIC_API_KEY"),
            max_tokens = 4096
        )

    def get_car_recommendation(self, criteria: dict) -> str:
        """
        Generuje rekomendację samochodu na podstawie kryteriów i danych z PDF.
        """
        # 1. Tworzenie zapytania do wyszukiwania w bazie wektorowej

        #search_query = (
        #    f"Marka: {criteria['car_producer']}, "
        #    f"Model: {criteria['car_model']}, "
        #    f"Wersja silnikowa: {criteria['engine']}, "
        #    f"Moc: {criteria['engine_power']}, "
        #    f"Klasa: {criteria['class']}, "
        #    f"Paliwo: {criteria['fuel_type']}, "
        #    f"Zużycie na 100km: {criteria['consumption']}, "
        #    f"Przeglądy co km: {criteria['service_interval']} km "
        #    f"Wyposażenie: {', '.join(criteria['equipment'])}, "
        #    f"Cena zakupu: {criteria['price_new']}, "
        #    f"Wartość po 1 roku: {criteria['price_1_year']}, "
        #    f"Wartość po 2 latach: {criteria['price_2_year']}, "
        #    f"Wartość po 3 latach: {criteria['price_3_year']}, "
        #    f"Wartość po 4 latach: {criteria['price_4_year']}, "
        #    f"Wartość po 5 latach: {criteria['price_5_year']}"
        #)
        car_classes_str = ", ".join(criteria['car_class'])
        fuel_types_str = ", ".join(criteria['fuel_type'])

        search_query = (
            f"Klasy: {car_classes_str}, "
            f"Paliwo: {fuel_types_str}, "
            f"Wyposażenie: {', '.join(criteria['equipment'])}, "
            f"Cena zakupu: {criteria['price_new']}, "
        )

        # 2. Pobieranie relevantnego kontekstu z bazy wektorowej
        context = self.rag_processor.find_relevant_context(search_query)

        if not context:
            return "Nie udało się znaleźć pasujących informacji w bazie danych. Spróbuj zmienić kryteria."

        # 3. Definicja szablonu promptu
        prompt_template = ChatPromptTemplate.from_template(
            """
            Jesteś ekspertem ds. flot samochodowych. Twoim zadaniem jest pomoc w wyborze idealnego samochodu na podstawie danych i kryteriów.
            
            **ZADANIE GŁÓWNE:** Twoja odpowiedź MUSI być kodem HTML. Użyj podanej struktury i klas CSS. Nie dołączaj tagów `<html>`, `<head>`, `<body>` ani ```html. Wygeneruj tylko kod HTML, który będzie można wstawić do istniejącej strony.**
            
            **KROK1: Przeanalizuj dostarczone dane:**
            
            * **Kontekst z bazy danych pojazdów**
            --- KONTEKST ---
            {context}
            --- KONIEC KONTEKSTU ---

            * ** Kryteria wyboru podane przez menedżera floty:**
            - Klasa samochodu: {car_class} - najważniejsze kryterium, nie podawaj aut z innych klas
            - Rodzaj paliwa: {fuel_type} - najważniejsze kryterium, nie podawaj samochodów z innymi rodzajami paliw
            - Maksymalna cena: {price_new} PLN
            - Wymagane wyposażenie: {equipment}
            - Okres eksploatacji: {exploitation_period} lat
            - Maksymalny przebieg: {max_mileage} km
            - Szacunkowy koszt jednego przeglądu: {service_cost} PLN
            - Ceny paliw: Benzyna={petrol_price} PLN/l, Diesel={diesel_price} PLN/l, Prąd={electricity_price} PLN/kWh

            **KROK 2: Wykonaj obliczenia TCO**
            Dla każdego pasującego samochodu w kontekście, wykonaj poniższe obliczenia. Przedstaw swoje obliczenia w sposób przejrzysty.

            1.  **Utrata Wartości:**
                a. Znajdź w kontekście cenę zakupu (`price_new`) oraz wartość rezydualną po `{exploitation_period}` latach.
                b. Oblicz: `Utrata Wartości = Cena Zakupu - Wartość Rezydualna`

            2.  **Koszt Paliwa:**
                a. Znajdź w kontekście zużycie paliwa (consumption). Upewnij się, że jednostki są poprawne (l/100km lub kWh/100km).
                b. Oblicz: `Koszt Paliwa = ({max_mileage} / 100) * Zużycie Paliwa * Cena Paliwa` (użyj odpowiedniej ceny dla danego typu paliwa).

            3.  **Koszt Serwisu:**
                a. Znajdź w kontekście interwał serwisowy - Przeglądy co km - (`service_interval`).
                b. Oblicz: `Koszt Serwisu = ({max_mileage} / Interwał Serwisowy) * Koszt Jednego Przeglądu`

            4.  **Całkowity Koszt Posiadania (TCO):**
                a. Oblicz: `TCO = Utrata Wartości + Koszt Paliwa + Koszt Serwisu`
                
            **KROK 3: Sformułuj rekomendację w formacie HTML**
            Użyj poniższej struktury HTML do sformatowania swojej odpowiedzi. Wypełnij ją wynikami swoich obliczeń.

            ```html
            <div class="analysis-container">
                <!-- Główna rekomendacja -->
                <div class="card recommendation-card">
                    <div class="card-header">
                        <span class="badge">Rekomendacja</span>
                        <h3>[Nazwa polecanego samochodu]</h3>
                    </div>
                    <div class="card-body">
                        <p>[Szczegółowe uzasadnienie, dlaczego ten samochód jest najlepszy pod kątem TCO. Odnieś się do obliczeń.]</p>
                        <h4>Analiza TCO dla [Nazwa polecanego samochodu]</h4>
                        <table class="tco-table">
                            <thead>
                                <tr>
                                    <th>Składnik TCO</th>
                                    <th>Obliczenia</th>
                                    <th>Koszt</th>
                                </tr>
                            </thead>
                            <tbody>
                                <tr>
                                    <td>Utrata Wartości</td>
                                    <td>[np. 150000 PLN - 75000 PLN]</td>
                                    <td>[np. 75000 PLN]</td>
                                </tr>
                                <tr>
                                    <td>Koszt Paliwa</td>
                                    <td>[np. (100000km / 100) * 5.5l * 6.00 PLN]</td>
                                    <td>[np. 33000 PLN]</td>
                                </tr>
                                <tr>
                                    <td>Koszt Serwisu</td>
                                    <td>[np. (100000km / 30000km) * 1200 PLN]</td>
                                    <td>[np. 3600 PLN]</td>
                                </tr>
                            </tbody>
                            <tfoot>
                                <tr>
                                    <td colspan="2">Całkowity Koszt Posiadania (TCO)</td>
                                    <td><strong>[np. 111600 PLN]</strong></td>
                                </tr>
                            </tfoot>
                        </table>
                    </div>
                </div>

                <!-- Alternatywy -->
                <h4>Rozważane alternatywy</h4>
                <div class="alternatives-grid">
                    <div class="card alternative-card">
                        <div class="card-header">
                            <h5>[Nazwa alternatywy 1]</h5>
                        </div>
                        <div class="card-body">
                            <p>[Krótkie uzasadnienie, dlaczego ten model jest gorszym wyborem. Porównaj jego TCO z rekomendowanym modelem.]</p>
                            <p><strong>Szacowane TCO: [Koszt TCO dla alternatywy 1]</strong></p>
                        </div>
                    </div>
                    <div class="card alternative-card">
                         <div class="card-header">
                            <h5>[Nazwa alternatywy 2]</h5>
                        </div>
                        <div class="card-body">
                            <p>[Krótkie uzasadnienie, dlaczego ten model jest gorszym wyborem.]</p>
                            <p><strong>Szacowane TCO: [Koszt TCO dla alternatywy 2]</strong></p>
                        </div>
                    </div>
                     <div class="card alternative-card">
                        <div class="card-header">
                            <h5>[Nazwa alternatywy 1]</h5>
                        </div>
                        <div class="card-body">
                            <p>[Krótkie uzasadnienie, dlaczego ten model jest gorszym wyborem. Porównaj jego TCO z rekomendowanym modelem.]</p>
                            <p><strong>Szacowane TCO: [Koszt TCO dla alternatywy 1]</strong></p>
                        </div>
                    </div>
                    <div class="card alternative-card">
                         <div class="card-header">
                            <h5>[Nazwa alternatywy 2]</h5>
                        </div>
                        <div class="card-body">
                            <p>[Krótkie uzasadnienie, dlaczego ten model jest gorszym wyborem.]</p>
                            <p><strong>Szacowane TCO: [Koszt TCO dla alternatywy 2]</strong></p>
                        </div>
                    </div>
                     <div class="card alternative-card">
                        <div class="card-header">
                            <h5>[Nazwa alternatywy 3]</h5>
                        </div>
                        <div class="card-body">
                            <p>[Krótkie uzasadnienie, dlaczego ten model jest gorszym wyborem. Porównaj jego TCO z rekomendowanym modelem.]</p>
                            <p><strong>Szacowane TCO: [Koszt TCO dla alternatywy 3]</strong></p>
                        </div>
                    </div>
                    <div class="card alternative-card">
                         <div class="card-header">
                            <h5>[Nazwa alternatywy 4]</h5>
                        </div>
                        <div class="card-body">
                            <p>[Krótkie uzasadnienie, dlaczego ten model jest gorszym wyborem.]</p>
                            <p><strong>Szacowane TCO: [Koszt TCO dla alternatywy 4]</strong></p>
                        </div>
                    </div>
                </div>
            </div>
            ```
            """
        )

        # 4. Formatowanie i wysłanie zapytania do AI
        chain = prompt_template | self.chat_model

        response = chain.invoke({
            "context": context,
            "car_class": criteria['car_class'],
            "fuel_type": criteria['fuel_type'],
            "equipment": ", ".join(criteria['equipment']) if criteria['equipment'] else "brak dodatkowych wymagań",
            "price_new": criteria['price_new'],
            #"service_interval": criteria['service_interval'],
            "exploitation_period": criteria['exploitation_period'],
            "max_mileage": criteria['max_mileage'],
            "service_cost": criteria['service_cost'],
            "petrol_price": criteria['petrol_price'],
            "diesel_price": criteria['diesel_price'],
            "electricity_price": criteria['electricity_price'],
        })

        # response = chain.invoke({
        #    "context": context,
        #    "car_producer": criteria['car_producer'],
        #    "car_model": criteria['car_model'],
        #    "engine": criteria['engine'],
        #    "engine_power": criteria['engine_power'],
        #    "car_class": criteria['car_class'],
        #    "fuel_type": criteria['fuel_type'],
        #   "consumption": criteria['consumption'],
        #    "service_interval": criteria['service_interval'],
        #    "equipment": ", ".join(criteria['equipment']) if criteria['equipment'] else "brak dodatkowych wymagań",
        #    "price_new": criteria['price_new'],
        #})

        return response.content

