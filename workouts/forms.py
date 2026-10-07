from django import forms
from django.forms import inlineformset_factory

from .models import Exercise, Muscle, Workout, WorkoutSet


# ==========================================
# 1. EXERCISE FORMS
# ==========================================

class ExerciseSearchForm(forms.Form):
    """Form for filtering and searching exercises by name, category, or muscles."""

    query = forms.CharField(
        required=False,
        label="Search",
        widget=forms.TextInput(attrs={
            'placeholder': 'Search exercise or muscle (e.g., Biceps, Push)...',
            'class': 'form-control'
        })
    )
    category = forms.ChoiceField(
        choices=[('', 'All Categories')] + Exercise.CATEGORY_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    target_muscles = forms.ModelMultipleChoiceField(
        queryset=Muscle.objects.all(),
        required=False,
        widget=forms.CheckboxSelectMultiple,
        label="Muscle Groups"
    )
    only_custom = forms.BooleanField(required=False, label="Only my custom exercises")


class ExerciseForm(forms.ModelForm):
    """Form for creating and updating the user's custom exercises."""

    class Meta:
        model = Exercise
        fields = ["name", "description", "category", "metric_type", "target_muscles"]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., Archer Push-ups'}),
            'description': forms.Textarea(attrs={'rows': 3, 'class': 'form-control', 'placeholder': 'Exercise instructions or notes...'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'metric_type': forms.Select(attrs={'class': 'form-select'}),
            'target_muscles': forms.CheckboxSelectMultiple,
        }
        help_texts = {
            'metric_type': 'How progress is measured: max reps, longest hold or heaviest added weight.',
        }

    def __init__(self, *args, user, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user

    def clean_name(self):
        name = self.cleaned_data['name'].strip()
        duplicates = Exercise.objects.available_for(self.user).filter(name__iexact=name)
        if self.instance.pk:
            duplicates = duplicates.exclude(pk=self.instance.pk)
        if duplicates.exists():
            raise forms.ValidationError("An exercise with this name already exists.")
        return name


# ==========================================
# 2. WORKOUT FORMS
# ==========================================

class WorkoutForm(forms.ModelForm):
    """Form for creating and updating workouts."""

    class Meta:
        model = Workout
        fields = ["started_at", "finished_at", "type", "notes"]
        widgets = {
            'started_at': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}, format='%Y-%m-%dT%H:%M'),
            'finished_at': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}, format='%Y-%m-%dT%H:%M'),
            'type': forms.Select(attrs={'class': 'form-select'}),
            'notes': forms.Textarea(attrs={'rows': 3, 'class': 'form-control', 'placeholder': 'How did the workout feel?'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        started_at = cleaned_data.get('started_at')
        finished_at = cleaned_data.get('finished_at')

        if started_at and finished_at and finished_at < started_at:
            raise forms.ValidationError("Finished time cannot be earlier than Started time!")

        return cleaned_data


class WorkoutSearchForm(forms.Form):
    """Form for filtering workouts in the journal."""

    type = forms.ChoiceField(
        choices=[('', 'All Types')] + Workout.WORKOUT_TYPE_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    muscle = forms.ModelChoiceField(
        queryset=Muscle.objects.all(),
        required=False,
        empty_label="All Muscle Groups",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    date_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )
    date_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )


# ==========================================
# 3. WORKOUT SET FORMS
# ==========================================

SET_WIDGETS = {
    'workout': forms.Select(attrs={'class': 'form-select'}),
    'exercise': forms.Select(attrs={'class': 'form-select'}),
    'set_number': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Auto'}),
    'reps': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Reps'}),
    'weight': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'kg', 'step': '0.5'}),
    'duration': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '00:00:30'}),
    'rest_time': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '00:01:00'}),
    'rpe': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '1–10', 'min': 1, 'max': 10}),
    'notes': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Optional note'}),
}


class SetFieldsMixin:
    """Restricts exercise choices to the user's catalog and checks the set has a result."""

    def limit_choices(self, user):
        self.fields['exercise'].queryset = Exercise.objects.available_for(user)

    def clean(self):
        cleaned_data = super().clean()
        exercise = cleaned_data.get('exercise')
        if exercise and not any(cleaned_data.get(f) not in (None, '') for f in ('reps', 'duration', 'weight')):
            raise forms.ValidationError("Enter reps, duration or weight for the set.")
        if exercise and exercise.metric_type == Exercise.METRIC_TIME and not cleaned_data.get('duration'):
            self.add_error('duration', "Hold exercises need a duration.")
        return cleaned_data


class WorkoutSetInlineForm(SetFieldsMixin, forms.ModelForm):
    """One set row inside the workout create/edit page."""

    class Meta:
        model = WorkoutSet
        fields = ["exercise", "reps", "weight", "duration", "rest_time", "rpe"]
        widgets = SET_WIDGETS

    def __init__(self, *args, user, **kwargs):
        super().__init__(*args, **kwargs)
        self.limit_choices(user)


class WorkoutSetForm(SetFieldsMixin, forms.ModelForm):
    """Standalone form for composing a single set with all its details."""

    class Meta:
        model = WorkoutSet
        fields = ["workout", "exercise", "set_number", "reps", "weight", "duration", "rest_time", "rpe", "notes"]
        widgets = SET_WIDGETS

    def __init__(self, *args, user, **kwargs):
        super().__init__(*args, **kwargs)
        self.limit_choices(user)
        self.fields['workout'].queryset = Workout.objects.filter(user=user)


WorkoutSetFormSet = inlineformset_factory(
    Workout,
    WorkoutSet,
    form=WorkoutSetInlineForm,
    extra=0,
    min_num=1,
    validate_min=True,
    can_delete=True,
)


class WorkoutSetSearchForm(forms.Form):
    """Filters for the workout sets journal."""

    exercise = forms.ModelChoiceField(
        queryset=Exercise.objects.none(),
        required=False,
        empty_label="All Exercises",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    muscle = forms.ModelChoiceField(
        queryset=Muscle.objects.all(),
        required=False,
        empty_label="All Muscle Groups",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    date_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )
    date_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )

    def __init__(self, *args, user, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['exercise'].queryset = Exercise.objects.available_for(user)
