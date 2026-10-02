from django import forms
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


class ExerciseForm(forms.ModelForm):
    """Form for creating and updating exercises."""

    class Meta:
        model = Exercise
        fields = ["name", "description", "category", "target_muscles"]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., Push-ups'}),
            'description': forms.Textarea(attrs={'rows': 3, 'class': 'form-control', 'placeholder': 'Exercise instructions or notes...'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'target_muscles': forms.SelectMultiple(attrs={'class': 'form-select'}),
        }


# ==========================================
# 2. WORKOUT FORMS
# ==========================================

class WorkoutForm(forms.ModelForm):
    """Form for creating and updating workouts."""

    class Meta:
        model = Workout
        fields = ["started_at", "finished_at", "type", "notes"]
        widgets = {
            'started_at': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
            'finished_at': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
            'type': forms.Select(attrs={'class': 'form-select'}),
            'notes': forms.Textarea(attrs={'rows': 3, 'class': 'form-control', 'placeholder': 'How did the workout feel?'}),
        }


class WorkoutSearchForm(forms.Form):
    """Form for filtering workouts in the journal."""

    type = forms.ChoiceField(
        choices=[('', 'All Types')] + Workout.WORKOUT_TYPE_CHOICES,
        required=False,
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

class WorkoutSetForm(forms.ModelForm):
    """Form for adding or editing an individual set inside a workout."""

    class Meta:
        model = WorkoutSet
        fields = ["exercise", "reps", "weight", "duration", "rest_time"]
        widgets = {
            'exercise': forms.Select(attrs={'class': 'form-select'}),
            'reps': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Reps'}),
            'weight': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Weight (lbs)'}),
            'duration': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '00:01:30'}),
            'rest_time': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '00:01:00'}),
        }