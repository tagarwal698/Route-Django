from django.shortcuts import render, redirect, reverse
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.auth import login, logout, authenticate
from django.conf import settings
from django.http import JsonResponse
from django.views.generic.edit import FormView
from django.views.generic.base import TemplateView
from django.utils.decorators import method_decorator

from Route.mixins import(
	AjaxFormMixin,
	reCAPTCHAValidation,
	FormErrors,
	RedirectParams
	)

from .forms import(
	UserForm,
	UserProfileForm,
	AuthForm,
	)


result = "error"
message = "This was an error. Please try again"


class AccountView(TemplateView):

	template_name = "users/account.html"

	@method_decorator(login_required)
	def dispatch(self, *args, **kwargs):   #this stops the unauthenticated user access
		return super().dispatch(*args, **kwargs)


def ProfileView(request):   #this is used to allow users to update their profile
	user = request.user
	up = request.userprofile

	form = UserProfileForm(instance = up)

	if request.is_ajax():
		form = UserProfileForm(data = request.POST, instance = up)
		if form.is_valid():
			obj = form.save()
			obj.has_profile = True
			obj.save()
			result = "Success"
			message = "Your profile has been updated"
		else:
			message = FormErrors(form)
		data = {'result' : result, 'message':message}
		return JsonResponse(data)

	else:

		context = {'form':form}
		context['google_api_key'] = settings.GOOGLE_API_KEY
		context['base_country'] = settings.BASE_COUNTRY

		return render(request, 'users/profile.html', context)

class SignUpView(AjaxFormMixin, FormView):
	 #Generic formview with our mixin for user signin and reCapture Security

	 template_name = "users/sign_up.html"
	 form_class = UserForm
	 success_url = "/"

	 #getting recapture key in context
	 def get_context_data(self, **kwargs):
	 	context = super().get_context_data(**kwargs)
	 	context["recaptcha_site_key"] = settings.RECAPTCHA_PUBLIC_KEY
	 	return context

	 #overwriting the mixing logic to get, check and save the recapture score

	 def form_valid(self, form):
	 	response = super(AjaxFormMixin, self).form_valid(form)
	 	if self.request.is_ajax():
	 		token = form.cleaned_data.get('token')
	 		captcha = reCAPTCHAValidation(token)
	 		if captcha["success"]:
	 			obj = form.save()
	 			obj.email = obj.username
	 			obj.save()
	 			up = obj.userprofile
	 			up.captcha_score = float(captach["score"])
	 			up.save()

	 			login(self.request, obj, backend = 'django.contrib.auth.backends.ModelBackend')


	 			#message on success
	 			result = "Success"
	 			message = "Thank you for signing up"

	 		data = {'result' : result, 'message' : message}
	 		return JsonResponse(data)

	 	return response

class SignInView(AjaxFormMixin, FormView):

	#Generic FormView with our mixin for user sign-in

	template_name = "users/sign_in.html"
	form_class = AuthForm
	success_url = "/"


	def form_valid(self, form):
		response = super(AjaxFormMixin, self).form_valid(form)
		if self.request.is_ajax():
			username = form.cleaned_data.get('username')
			password = form.cleaned_data.get('password')
			#authenticating the user
			user = authenticate(self.request, username = username, password = password)
			if user is not None:
				login(self.request, user, backend = 'django.contrib.auth.backends.ModelBackend')
				result = "Success"
				message = "You are not logged in."
			else:
				message.FormErrors(form)
			data = {'result':result, 'message' : message}
			return JsonResponse(data)
		return response


def sign_out(request):
	#Basic function based view to signout

	logout(request)
	return redirect(reverse('users:sign-in'))