from django.shortcuts import render, redirect, reverse
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponseRedirect
from .models import Question, Answer, Text, Consent
from django.contrib.auth.forms import AuthenticationForm
from analytics.models import UserEventLog
from analytics.utils import create_event_log
from configuration.models import get_the_config
from articles.models import Article

import json

@login_required
def redirect_to_questions(request):
    config = get_the_config()
    # Prüfen, ob es unbeantwortete "before"-Fragen gibt
    unanswered_questions = Question.objects.filter(label='before').exclude(
        id__in=Answer.objects.filter(user=request.user).values_list('question_id', flat=True)
    )
    
    # Wenn unbeantwortete Fragen existieren, dorthin weiterleiten
    if unanswered_questions.exists():
        return redirect('questions:questions_before')
    
    request.session['start_view'] = config.start_view

    # Andernfalls zu einer anderen Seite (z. B. Dashboard oder Newspaper)
    if config.start_view == 'article_list' and config.start_newspaper_id:
        return redirect('articles:all-articles',
                       news_paper_id=config.start_newspaper_id)

    elif config.start_view == 'article' and config.start_article_id:
        # Artikel aus der Datenbank holen um news_paper_id und slug zu bekommen
        try:
            article = Article.objects.get(id=config.start_article_id)
            return redirect('articles:detailed-article',
                           news_paper_id=article.news_paper_id,
                           slug=article.slug)
        except Article.DoesNotExist:
            # Fallback zur Zeitungsübersicht wenn Artikel nicht gefunden
            return redirect('articles:news-papers')

    else:
        return redirect('articles:news-papers')

from django.shortcuts import render, redirect
from .models import Question, Answer
from django.contrib.auth.decorators import login_required
from django.contrib import messages

@login_required
def question_list(request, label):

    # Alle Fragen und beantwortete Fragen filtern
    questions = Question.objects.filter(label=label).order_by('order')
    answered_questions = Answer.objects.filter(
        user=request.user, question__label=label
    ).values_list('question_id', flat=True)
    unanswered_questions = questions.exclude(id__in=answered_questions)

    for question in unanswered_questions:
        if question.question_type == 'slider' and question.min_value is not None and question.max_value is not None:
            question.mid_value = (question.min_value + question.max_value) // 2

    # POST-Request (Antworten speichern)
    if request.method == 'POST':
        for question in unanswered_questions:
            field_name = f'question_{question.id}'
            if question.question_type == 'multiple_choice':
                answers = request.POST.getlist(field_name)
                if question.required and not answers:
                    messages.error(
                        request, f"Bitte beantworten Sie die Frage: {question.question_text}"
                    )
                    return render(
                        request, 'questions/question_list.html',
                        {'questions': unanswered_questions, 'label': label}
                    )
                for answer_text in answers:
                    Answer.objects.create(
                        question=question, user=request.user, answer_text=answer_text
                    )
                
            elif question.question_type == 'slider':
                answer_value = request.POST.get(field_name)
                if question.required and not answer_value:
                    messages.error(request, f"Bitte beantworten Sie die Frage: {question.question_text}")
                    return render(request, 'questions/question_list.html', {'questions': unanswered_questions, 'label': label})
                Answer.objects.create(question=question, user=request.user, answer_text=answer_value)

            elif question.question_type == 'multiple_likert':
                for sub_question in question.get_sub_questions():
                    sub_field_name = f'{field_name}_{sub_question}'
                    answer_value = request.POST.get(sub_field_name)
                    if question.required and not answer_value:
                        messages.error(request, f"Bitte beantworten Sie die Frage: {sub_question}")
                        return render(request, 'questions/question_list.html', {'questions': unanswered_questions, 'label': label})
                    
                    Answer.objects.create(
                        question=question,
                        user=request.user,
                        sub_question=f"Sub_question:{sub_question}",
                        answer_text=answer_value
                    )
            elif question.question_type == 'ampel_rating':
                # Alle Antworten für die Frage sammeln
                for index, pair in enumerate(question.get_subchoice_pairs()):
                    field_name = f"question_{question.id}_{index + 1}"  # parentloop.counter startet bei 1!
                    print(field_name)
                    answer_value = request.POST.get(field_name)
                    print(f"Erwarteter Feldname: {field_name}, Wert: {answer_value}")


                    # Validierung: Pflichtfeld prüfen
                    if question.required and not answer_value:
                        messages.error(
                            request, 
                            f"Bitte beantworten Sie die Zeile '{pair[0]}' in der Frage: {question.question_text}"
                        )
                        return render(request, 'questions/question_list.html', {'questions': unanswered_questions, 'label': label})

                    # Antwort erstellen und speichern (innerhalb der Schleife)
                    Answer.objects.create(
                        question=question,
                        user=request.user,
                        sub_question=f"Sub_choices:{pair}",
                        answer_text=answer_value
                    )
                            
            else:
                answer_text = request.POST.get(field_name, '')
                if question.required and not answer_text:
                    messages.error(
                        request, f"Bitte beantworten Sie die Frage: {question.question_text}"
                    )
                    return render(
                        request, 'questions/question_list.html',
                        {'questions': unanswered_questions, 'label': label}
                    )
                Answer.objects.create(
                    question=question, user=request.user, answer_text=answer_text
                )

        # Nach dem Speichern die unbeantworteten Fragen neu berechnen
        answered_questions = Answer.objects.filter(
            user=request.user, question__label=label
        ).values_list('question_id', flat=True)
        unanswered_questions = questions.exclude(id__in=answered_questions)

        # Weiterleitung nach Beantwortung aller `before`-Fragen
        if not unanswered_questions.exists():

            if label == 'before':
                config = get_the_config()
                request.session['start_view'] = config.start_view
                # Andernfalls zu einer anderen Seite (z. B. Dashboard oder Newspaper)
                if config.start_view == 'article_list' and config.start_newspaper_id:
                    return redirect('articles:all-articles',
                                news_paper_id=config.start_newspaper_id)

                elif config.start_view == 'article' and config.start_article_id:
                    # Artikel aus der Datenbank holen um news_paper_id und slug zu bekommen
                    try:
                        article = Article.objects.get(id=config.start_article_id)
                        return redirect('articles:detailed-article',
                                    news_paper_id=article.news_paper_id,
                                    slug=article.slug)
                    except Article.DoesNotExist:
                        # Fallback zur Zeitungsübersicht wenn Artikel nicht gefunden
                        return redirect('articles:news-papers')

                else:
                    return redirect('articles:news-papers')
            elif label == 'after':
                return redirect('questions:experiment_end')

    # Alle Fragen beantwortet: Sofort weiterleiten
    if not unanswered_questions.exists():
        messages.success(request, "Vielen Dank, Ihre Antworten wurden erfolgreich gespeichert!")
        if label == 'before':
            return redirect('articles:news-papers')
        elif label == 'after':
            return redirect('questions:experiment_end')
        
        
    ##Helping functions:

    questions_with_pairs = [
        {'question': q, 'subchoice_pairs': q.get_subchoice_pairs(), 'choices': q.get_choices()}
        for q in questions
    ]
    
    if question.range_value:  # Überprüfen, ob range_value nicht None ist
        try:
            range_10 = [int(value) for value in question.range_value.split(';') if value.strip()]
        except ValueError:
            messages.error(request, f"Ungültige Werte im Range für Frage: {question.question_text}")
            range_10 = range(10)  # Standardwert setzen
    else:
        range_10 = range(10)  # Standardwert, falls range_value nicht gesetzt ist


    #Context

    context = {
    'questions': unanswered_questions,
    'label': label,
    'range_10': range_10,
    'questions_with_pairs': questions_with_pairs, 
    'is_questions_page': request.path.startswith("/questions/")
}

    # Offene Fragen anzeigen
    return render(request, 'questions/question_list.html', context)


##Start View
def experiment_start(request):
    return render(request, 'questions/start.html')

def participant_info(request):
    # Fetch the content based on identifier and visibility
    participant_info_header = Text.objects.filter(visibility=True, identifier__startswith="participant_info_header").first()
    participant_info_message = Text.objects.filter(visibility=True, identifier__startswith="participant_info_message").first()

    return render(request, 'questions/participant_info.html', {
        'participant_info_header': participant_info_header.content if participant_info_header else "Participant information header (default - please change).",
        'participant_info_message': participant_info_message.content if participant_info_message else "Participant information message (default - please change).",

    })

# View for displaying the Consent Form (Einverständniserklärung)
def consent_form(request):
    consent_form_header = Text.objects.filter(visibility=True, identifier__startswith="consent_form_header").first()
    consent_form_message = Text.objects.filter(visibility=True, identifier__startswith="consent_form_message").first()

    if request.method == 'POST':
        consent_given = request.POST.get('consent', 'no')

        if consent_given == 'yes':
            # Save user consent to the database
            # Consent.objects.create(user=request.user, consent_given=True)

            return HttpResponseRedirect(reverse('questions:redirect_to_questions'))  # Redirect to the experiment start page (login)
        elif consent_given == 'no':
            return redirect('questions:not_eligible')

    return render(request, 'questions/consent_form.html', {
        'consent_form_header': consent_form_header.content if consent_form_header else "Consent form header (default - please change)",
        'consent_form_message': consent_form_message.content if consent_form_message else "Consent form is currently not available. (default - please change)",
    })

def not_eligible(request):
    no_consent_message = Text.objects.filter(visibility=True, identifier__startswith="no_consent_message").first()

    return render(request, 'questions/not_eligible.html', {
         'no_consent_message': no_consent_message.content if no_consent_message else "You have opted not to participate in the study. Thank you for your time. (default - please change)"
    })

def experiment_end(request):
    
    # Fetch visible text content without language dependency
    end_header = Text.objects.filter(visibility=True, identifier__startswith="end_experiment_header_").first()
    end_message = Text.objects.filter(visibility=True, identifier__startswith="end_experiment_message_").first()

    return render(request, 'questions/end.html', {
        'end_experiment_header': end_header.content if end_header else "End of the Experiment (default - please change)",
        'end_experiment_message': end_message.content if end_message else "Thank you for participating in our study! You can now close this page. (default - please change)",
    })

from allauth.account.forms import LoginForm

def custom_login_view(request):
    form = LoginForm(request.POST or None)
    # Pass a boolean value to the context
    is_registration_disabled = True  # or some logic to determine this
    return render(request, 'account/login.html', {'form': form, 'is_registration_disabled': is_registration_disabled})

    # disable_custom = request.GET.get('disable_custom', 'false').lower() == 'true'
    # return redirect('accounts:login')