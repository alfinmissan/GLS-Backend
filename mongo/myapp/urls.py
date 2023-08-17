"""mongo URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from django.contrib.auth import views as auth_views
from django.urls import path, include,re_path
from . import views
from . import logs
from rest_framework import routers
from .views import UserViewSet,AssetViewSet,FontViewSet,\
    AttachmentViewSet,GridDocumentAttachments, GridCommentAndFileAttachments,ArtWorkViewSet,SalesReportViewSet

router = routers.DefaultRouter()
router.register('user', UserViewSet, basename='login')
router.register('ast', AssetViewSet, basename='asset')
router.register('artwork', ArtWorkViewSet, basename='artwork')
router.register('salesReport', SalesReportViewSet, basename='salesReport')
router.register('font', FontViewSet, basename='font')
router.register('attachment', AttachmentViewSet, basename='attachment')
router.register('grid/attachments', GridCommentAndFileAttachments, basename='gird/attchment')
router.register('grid/documents', GridDocumentAttachments, basename='gird/documents')
schema_view = get_schema_view(
   openapi.Info(
      title="Snippets API",
      default_version='v1',
      description="Test description",
      terms_of_service="https://www.google.com/policies/terms/",
      contact=openapi.Contact(email="contact@snippets.local"),
      license=openapi.License(name="BSD License"),
   ),
   public=True,
   permission_classes=[permissions.AllowAny],
)


urlpatterns = [
    #path('swagger/', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    #path('', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
    path('url/', include(router.urls)),
    path('translation', views.addUpdateDelTranslations),
    path('mastercode', views.masterCodeVIewAddDelUpdate),
    path('factory', views.factoryAddViewDelUpdate),
    path('lang', views.languageAddViewDelUpdate),
    path('country', views.counrtyViewAddDelUpdate),
    path('req/view', views.viewRequirement),
    path('req', views.AddDelUpdateRequirements),
    path('blend', views.addViewDelUpdateBlend),
    path('legalName', views.addViewDelUpdateLegalName),
    path('grid', views.gridUpdateDeleteAdd),
    path('range', views.selectRange),
    path('category', views.categoryAddDeleteView),
    path('tea.bag', views.noOfTeaBag),
    path('custom/condition', views.CustomCondtionView),
    path('version/change', views.transVersionChange),
    path('grid/version',views.gridVersion),
    path('inputModule/log',logs.Log_input_mudules),
    path('inputModule/reg/log', logs.Log_input_mudules_reg),
    path('inputModule/blend/log', logs.blend_requirement_history),
    path('grid/log',logs.log_grid_module),
    path('viewer/report',views.grid_viewer_report),
    path('grid/report',views.grid_report),
    path('task/view',logs.task_view),
    path('mail',views.Email),
    path('sub/traslation',views.Subtranslation),
    path('dboard',views.Dashboard),
    path('trans/version',views.translationVerions),
    path('excel/import',views.ExcelView.as_view()),
    path('translation/import',views.TranslationImportView.as_view()),
    path('get/font',views.get_font_name),
    path('text/translations',views.text_translation),
    path('lang/codes',views.languageCodes),
    path('req/dropdown',views.requirementDropdownvalues),
    path('lan/list',views.languageDropdownvalues),
    path('req/search',views.SearchRequirement),
    path('factory/excel',views.FactoryExcel),
    path('ast/delete',views.deleteAsset),
    path('country/requirement/dropdown',views.CountryrequirementDropdownvalues),
    path('country/requirement',views.AddCountryRequirement),
    path('mastercode/import',views.MasterCodeImportView.as_view()),
    path('country/exprtimport',views.CountryImportExport.as_view()),
    path('importexport/requirements',views.RequirementImportExport.as_view()),
    path('import/exportBlendRequirements',views.BlendRequirementImportExport.as_view()),
    path('import/exportItemRequirements', views.ItemRequirementImportExport.as_view()),
    path('importexport/blend',views.BlendImportView.as_view()),
    path('importexport/legalname',views.LegalNameImportView.as_view()),
    path('importexport/itemNo',views.ItemNoImportExportView.as_view()),
    path('importexport/regno',views.RegNoImportExportView.as_view()),
    path('username',views.UserName),
    path('grid/dropdown',views.GridValuesDropDown),
    path('user/groupedview',views.userGroupedView),
    path('factory/dropdown',views.FactorydropDown),
    path('ingredients/dropdown',views.IngredientsDropdownvalues),
    path('grid/test',views.testGrid),
    path('grid/history',views.GridHistory),
    path('graph/data',views.GraphData),
    path('post/comment',views.AddComment),
    path('grid/addlan',views.GridNewLanguage),
    path('grid/addrequirement',views.GridNewRequirement),
    path('weight', views.Weights),
    path('teaform', views.TeaBagForm),
    path('assettype', views.AssetType),
    path('fontlist', views.get_fonts),
    path('update/user',views.UpdateUser),
    path('customcondition/dropdown', views.CustomConditonDropdown),
    path('grid/flow',logs.GridFlowInformation),
    path('view/notification', logs.ViewNotification),
    path('enable/condition',views.enable_disable_condition),
    path('grid/commentView',views.gridCommentAttachmentView),
    path('grid/duplicate',views.saveDuplicateGrid),
    path('home/graph',views.TaskGraphData),
    path('task/search',views.task_list_search),
    path('doc/view',views.ViewDocuments),
    path('search/user',views.search_user),
    path('varient/check', logs.gridvarientCheck),
    path('log/duplicate',logs.grid_duplicate_logs),
    path('country/requirement/export',views.CountryBaseRequirementExport),
    path('auth/admin',views.CheckAuthorizedAdmin),
    path('auth/user',views.CheckAuthorized),
    path('export/texttranslations',views.MasterCodeTranslations),
    # Forget Password
    path('password-reset/',
         auth_views.PasswordResetView.as_view(
             template_name='commons/password-reset/password_reset.html',
             subject_template_name='commons/password-reset/password_reset_subject.txt',
             email_template_name='commons/password-reset/password_reset_email.html',
             success_url='/password-reset/done/'
         ),
         name='password_reset'),
    path('password-reset/done/',
         auth_views.PasswordResetDoneView.as_view(
             template_name='commons/password-reset/password_reset_done.html'
         ),
         name='password_reset_done'),
    path('password-reset-confirm/<uidb64>/<token>/',
         auth_views.PasswordResetConfirmView.as_view(
             template_name='commons/password-reset/password_reset_confirm.html'
         ),
         name='password_reset_confirm'),
    path('password-reset-complete/',
         auth_views.PasswordResetCompleteView.as_view(
             template_name='commons/password-reset/password_reset_complete.html'
         ),
         name='password_reset_complete'),
    path('customCondtion/Coustrybased/<str:country>/', views.CountryBasedCustomConditionView.as_view()),
    path('blendRequirements',views.blend_requirements),
    path("itemrequirement",views.item_requirements),
    path('get_artwork', views.retrieve_artwork),
    path('search_version', views.get_traslationVersions),
    path('itemNo', views.ItemNoModule),
    path('registrationNo', views.RegistrationNo),
    path('get/report', views.get_report),
    path('grouped/translation', views.groupdeTranslations),
    path('delete/all', views.deleteModule)
]
