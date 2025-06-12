import os
from langchain_anthropic import ChatAnthropic
from langchain.prompts import ChatPromptTemplate
from .rag_processor import RAGProcessor


class AnthropicService:
    def __init__(self):
        self.rag_processor = RAGProcessor()
        self.chat_model = ChatAnthropic(
            model="claude-3-7-sonnet-20250219",  # Możesz wybrać inny model, np. Haiku
            api_key=os.getenv("ANTHROPIC_API_KEY")
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

            Przeanalizuj poniższy kontekst, który pochodzi z naszej wewnętrznej bazy danych pojazdów:
            --- KONTEKST ---
            {context}
            --- KONIEC KONTEKSTU ---

            Oto kryteria wyboru podane przez menedżera floty:
            - Klasa samochodu: {car_class}
            - Rodzaj paliwa: {fuel_type}
            - Maksymalna cena: {price_new} PLN
            - Wymagane wyposażenie: {equipment}

            Twoje zadanie:
            1. Zarekomenduj jeden, najlepszy model samochodu, który spełnia jak najwięcej z powyższych kryteriów.
            2. Przedstaw szczegółowe uzasadnienie swojego wyboru, odnosząc się do danych z kontekstu.
            3. Opcjonalnie, zaproponuj 3-4 alternatywne modele, jeśli istnieją, i krótko je porównaj z główną rekomendacją.
            4. Odpowiedź sformatuj w języku polskim, w sposób przejrzysty i czytelny.
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

