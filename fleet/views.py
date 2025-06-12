from django.shortcuts import render
from .forms import CarDataForm  # Zmieniono import
from .services.anthropic_service import AnthropicService


def car_selection_view(request):
    form = CarDataForm()  # Zmieniono formularz
    result = None

    if request.method == 'POST':
        form = CarDataForm(request.POST)  # Zmieniono formularz
        if form.is_valid():
            criteria = form.cleaned_data

            anthropic_service = AnthropicService()
            result = anthropic_service.get_car_recommendation(criteria)

            return render(request, 'fleet/results.html', {
                'criteria': criteria,
                'result': result
            })

    return render(request, 'fleet/index.html', {'form': form})
