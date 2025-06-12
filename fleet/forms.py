from django import forms

CLASS_CHOICES = [
    ('A', 'Klasa A (miejskie)'), ('B', 'Klasa B (małe)'), ('C', 'Klasa C (kompakty)'),
    ('D', 'Klasa D (średnie)'), ('E', 'Klasa E (wyższe)'), ('SUV', 'SUV')
]

FUEL_TYPE_CHOICES = [
    ('benzyna', 'Benzyna'), ('diesel', 'Diesel'),
    ('hybryda', 'Hybryda'), ('elektryczny', 'Elektryczny')
]

EQUIPMENT_CHOICES = [
    ('klimatyzacja automatyczna', 'Klimatyzacja automatyczna'),
    ('skórzana tapicerka', 'Skórzana tapicerka'),
    ('nawigacja GPS', 'Nawigacja GPS'),
    ('kamera cofania', 'Kamera cofania'),
    ('aktywny tempomat', 'Aktywny tempomat'),
    ('podgrzewane fotele', 'Podgrzewane fotele'),
]


class CarDataForm(forms.Form):
    #car_producer = forms.CharField(label="Marka pojazdu", max_length=100)
    #car_model = forms.CharField(label="Model pojazdu", max_length=100)
    #engine = forms.CharField(label="Wersja silnikowa", max_length=100)
    #engine_power = forms.IntegerField(label="Moc (KM)", min_value=1)

    car_class = forms.MultipleChoiceField(
        choices=CLASS_CHOICES,
        widget=forms.SelectMultiple(attrs={'class': 'tom-select-multiple'}),
        label="Klasa samochodu - można wybrać kilka",
        required=False
    )
    fuel_type = forms.MultipleChoiceField(
        choices=FUEL_TYPE_CHOICES,
        widget=forms.SelectMultiple(attrs={'class': 'tom-select-multiple'}),
        label="Rodzaj paliwa - można wybrać kilka",
        required=False
    )
    #consumption = forms.DecimalField(label="Zużycie paliwa (l/100km)", min_value=0, decimal_places=1)
    #service_interval = forms.IntegerField(label="Przeglądy co (km)", min_value=1000)

    equipment = forms.MultipleChoiceField(
        choices=EQUIPMENT_CHOICES,
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'tom-select-multiple'}),
        label="Wyposażenie (opcjonalne)",
        required=False
    )

    price_new = forms.IntegerField(label="Cena zakupu (PLN)", min_value=0, widget=forms.NumberInput(attrs={'class': 'form-input'}))

    # Parametry do analizy TCO
    exploitation_period = forms.IntegerField(label="Okres eksploatacji (lata)", min_value=1, max_value=5,
                                             widget=forms.NumberInput(attrs={'class': 'form-input'}))
    max_mileage = forms.IntegerField(label="Maksymalny zakładany przebieg (km)", min_value=1000,
                                     widget=forms.NumberInput(attrs={'class': 'form-input'}))
    service_cost = forms.IntegerField(label="Szacunkowy koszt jednego przeglądu (PLN)", min_value=0,
                                      widget=forms.NumberInput(attrs={'class': 'form-input'}))

    # Ceny paliw
    petrol_price = forms.DecimalField(label="Cena benzyny (PLN/l)", initial=6.00, min_value=0, decimal_places=2,
                                      widget=forms.NumberInput(attrs={'class': 'form-input'}))
    diesel_price = forms.DecimalField(label="Cena oleju napędowego (PLN/l)", initial=6.00, min_value=0,
                                      decimal_places=2, widget=forms.NumberInput(attrs={'class': 'form-input'}))
    electricity_price = forms.DecimalField(label="Cena energii elektrycznej (PLN/kWh)", initial=1.80, min_value=0,
                                           decimal_places=2, widget=forms.NumberInput(attrs={'class': 'form-input'}))