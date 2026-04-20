from django import forms
from .models import Comment
from django.utils.translation import gettext_lazy as _

class CommentModelForm(forms.ModelForm):
    title = forms.CharField(
        label=_("Title"),
        widget=forms.TextInput(
            attrs={
                'placeholder': _("Enter the title of your comment"),
                'style': 'background-color: #F0F2F5;'
            }
        ),
        initial=_("Default Title")  # Default value for title
    )
    content = forms.CharField(
        label='',
        widget=forms.Textarea(
            attrs={
                'rows': 3,
                'placeholder': _("comment_creation_prompt"),
                'style': 'background-color: #F0F2F5;'
            }
        ),
        initial=_("Default comment content")  # Default value for content
    )
    side = forms.ChoiceField(
        choices=[('pro', 'Pro'), ('contra', 'Contra')],
        widget=forms.RadioSelect,
        required=False,
        label="Position"
    )

    class Meta:
        model = Comment
        fields = ('title', 'content')

class SecondaryCommentModelForm(forms.ModelForm):
    title = forms.CharField(
        label=_("Reply Title"),
        widget=forms.TextInput(
            attrs={
                'placeholder': _("Enter the title of your reply"),
                'style': 'background-color: #F0F2F5;'
            }
        ),
        initial=_("Default Reply Title")  # Default value for reply title
    )
    content = forms.CharField(
        label='',
        widget=forms.TextInput(
            attrs={
                'placeholder': _("reply_creation_prompt"),
                'style': 'background-color: #F0F2F5;'
            }
        ),
        initial=_("Default reply content")  # Default value for reply content
    )

    class Meta:
        model = Comment
        fields = ('title', 'content')
