from rest_framework import serializers
from .models import CustomUser, Asset, Fonts
from .models import Attachment, ArtWorks, SalesReport
from rest_framework.authtoken.models import Token
from rest_framework.fields import ListField

class UserSerialiser(serializers.ModelSerializer):
    password = serializers.CharField(
        style={'input_type': 'password'},
        write_only=True
    )
    class Meta:
        model = CustomUser
        fields = ['username','password','first_name','last_name','email','designation','user_group','country','id']
        extra_kwargs = {'password':{'write_only':True,'required':True}}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance:
            self.fields.pop('password')
    def create(self, validated_data):
        user = CustomUser.objects.create_user(**validated_data)
        Token.objects.create(user=user)
        return user



class TranslationSerializers(serializers.Serializer):
    language = serializers.CharField(max_length=10)
    text = serializers.CharField()
    trans = serializers.CharField(max_length=5000)
    tran_id = serializers.CharField(max_length=100)
    master_id = serializers.CharField(max_length=100)
class TranslationUpdateSerializer(serializers.Serializer):
    language = serializers.CharField(max_length=10,allow_null=False)
    master_id = serializers.CharField(max_length=15,allow_null=False)
    trans = serializers.CharField(max_length=100,allow_null=False)
class LanguageSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=100,min_length=1,allow_null=False)
    code = serializers.CharField(max_length=8,min_length=1,allow_null=False)
class CountrySerializer(serializers.Serializer):
    name = serializers.CharField(max_length=40,min_length=1,allow_null=False)
    code = serializers.CharField(max_length=8,min_length=1,allow_null=False)
    language =serializers.ListField(allow_empty=False)
class CountryUpdateSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=40,min_length=1)
    code = serializers.CharField(max_length=8,min_length=1)
    id = serializers.CharField(max_length=50)
    language = ListField(allow_empty=False)
class BlendSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=50,min_length=2, allow_blank=False)
    blend_tea_bag= serializers.CharField(min_length=1,allow_blank=True)
    blend_loose = serializers.CharField(allow_blank=True)
    ingredient_tea_bag = serializers.CharField(allow_blank=True)
    ingredient_loose = serializers.CharField(allow_blank=True)
    tea_origin = serializers.CharField(allow_blank=True)
    range = serializers.CharField(max_length=20, allow_blank=False)
class BlendUpdateSerializer(serializers.Serializer):
    id=serializers.CharField(max_length=100,min_length=2,allow_blank=False)
    name = serializers.CharField(max_length=50, min_length=2, allow_blank=False)
    blend_tea_bag = serializers.CharField(min_length=1, allow_blank=True)
    blend_loose = serializers.CharField(allow_blank=True)
    ingredient_tea_bag = serializers.CharField(min_length=1,allow_blank=True)
    ingredient_loose = serializers.CharField(allow_blank=True)
    tea_origin = serializers.CharField(max_length=50, allow_blank=True)
    range = serializers.CharField(max_length=20, allow_blank=True)
class IngredientSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=50,min_length=2, allow_blank=False)
    tea_bag = serializers.CharField(max_length=50,allow_blank=True)
    loose_trans = serializers.CharField(max_length=200,allow_blank=True)
class IngredientUpdateSerializer(serializers.Serializer):
    id = serializers.CharField(max_length=100,min_length=2,allow_blank=False)
    name = serializers.CharField(max_length=50, min_length=1, allow_blank=False)
    tea_bag = serializers.CharField(max_length=50,allow_blank=True)
    loose_trans = serializers.CharField(max_length=200,allow_blank=True)
class LegalNameSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=100,allow_blank=False)
    translation = serializers.CharField(max_length=100, allow_blank=True)
class LegalNameUpdateSerializer(serializers.Serializer):
    id = serializers.CharField(max_length=100,min_length=2,allow_blank=False)
    name = serializers.CharField(max_length=100,min_length=1,allow_blank=False)
class AssetUpload(serializers.Serializer):
    type = serializers.CharField(max_length=50,allow_blank=False)
    name = serializers.CharField(max_length=50,allow_blank=False)
    photo = serializers.ImageField()
class AssetSerializer(serializers.ModelSerializer):
    class Meta:
        model = Asset
        fields = ['name','photo','type','id']
class FactorySerializer(serializers.Serializer):
    location = serializers.DictField(allow_empty=False)
    packed_in = serializers.DictField(allow_empty=False)
    address = serializers.DictField(allow_empty=False)
class FactoryUpdateSerializer(serializers.Serializer):
    id = serializers.CharField(max_length=100,allow_blank=False)
    location = serializers.DictField(allow_empty=False)
    packed_in = serializers.DictField(allow_empty=False)
    address = serializers.DictField(allow_empty=False)
class RequirementSerializers(serializers.Serializer):
    requirement = serializers.CharField(max_length=100,allow_blank=False)
    type = serializers.CharField(max_length=15)
    value = serializers.CharField(max_length=100, allow_blank=True)
    country = ListField()
    static = serializers.BooleanField()
    order = serializers.IntegerField(allow_null=False)
    def validate(self, attrs):
        static = attrs.get('static')
        if static is None:
            raise serializers.ValidationError("Static field cannot be empty.")
        return attrs
class CountryRequirementSerializers(serializers.Serializer):
    id = serializers.CharField(max_length=100,allow_blank=False)
    country = serializers.CharField(max_length=15)

class RequirementUpdateSerializers(serializers.Serializer):
    id = serializers.CharField(max_length=60)
    requirement = serializers.CharField(max_length=100,allow_blank=False)
    type = serializers.CharField(max_length=15)
    value = serializers.CharField(max_length=1000, allow_blank=True)
    country = ListField()
    static = serializers.BooleanField()
    order = serializers.IntegerField(allow_null=False)
    def validate(self, attrs):
        static = attrs.get('static')
        if static is None:
            raise serializers.ValidationError("Static field cannot be empty.")
        return attrs
class GridSerializer(serializers.Serializer):
    job = serializers.CharField(max_length=50, allow_blank=False)
    item = serializers.IntegerField()
    varient = serializers.CharField(max_length=50, allow_blank=False)
    type = serializers.CharField(max_length=50, allow_blank=False)
    countries = ListField(allow_empty=False)
    range = serializers.CharField(max_length=30,allow_blank=True)
    blends = serializers.JSONField(allow_null=False)
    additional_lan = serializers.CharField(allow_blank=True, required=False)
    tea_form = serializers.CharField(max_length=50, required=False)
    Description = serializers.CharField(max_length=200, allow_blank=False)
    legal_name = serializers.CharField(max_length=50,allow_blank=True)
    category = serializers.CharField(max_length=50,allow_blank=True)
    weight = serializers.CharField(max_length=50,allow_blank=True)
    no_of_bags = serializers.CharField(allow_blank=True)
    factory = serializers.DictField()

class SaveGridSerializer(serializers.Serializer):
    data = serializers.ListField()
    translation = serializers.ListField()
    special_requirement = serializers.CharField(allow_blank=True,required=False)
    gridinformations = serializers.CharField(allow_blank=True, required=False)
    grouped_translation = serializers.DictField()
    # date = serializers.DateField()
    languages = serializers.ListField()
    user = serializers.CharField()
    grid = serializers.JSONField()
class CustomCondtionSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=50)
    mainLogc= ListField()
    subLogic = ListField()
    statement =  ListField()
    state = serializers.BooleanField(default=True)
    output = serializers.DictField()
class CustomCondtionUpdateSerializer(serializers.Serializer):
    id = serializers.CharField(max_length=50)
    name = serializers.CharField(max_length=50)
    mainLogc = ListField()
    subLogic = ListField()
    statement = ListField()
    state = serializers.BooleanField(default=True)
    output = serializers.DictField()
class GridVersionAddSerializer(serializers.Serializer):
    varient = serializers.CharField(max_length=50)
    item = serializers.IntegerField()
    grid = serializers.JSONField()
    translations = serializers.ListField()
class GridDuplicateSerilaizer(serializers.Serializer):
    varient = serializers.CharField(max_length=60)
    item =serializers.IntegerField()
    job = serializers.CharField(max_length=50, allow_blank=False)
    country = ListField()
    grid =serializers.JSONField()
    factory = serializers.CharField(max_length=10)
class InputLogSerializer(serializers.Serializer):
    user = serializers.CharField(max_length=20)
    action =serializers.DictField()
    module = serializers.CharField(max_length=20)
class GridLogSerializer(serializers.Serializer):
    user = serializers.CharField(max_length=20)
    varient = serializers.CharField(max_length=20)
    item = serializers.CharField(max_length=20)
    status = serializers.CharField(max_length=50)
    log = serializers.IntegerField()
class FontSerializer(serializers.ModelSerializer):
    class Meta:
        model = Fonts
        fields = ['name','font','language']
class LanguageUpdateSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=100)
    code = serializers.CharField(max_length=15)
    id = serializers.CharField(max_length=100)

class AttachmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Attachment
        fields = '__all__'

class ExcelSerializer(serializers.Serializer):
    files = serializers.FileField(allow_empty_file=False)

class TranslationImportExcelSerializer(serializers.Serializer):
    files = serializers.FileField()
    language = serializers.CharField(max_length=4)

class CountryImportSerializer(serializers.Serializer):
    files = serializers.FileField()

class DeleteMastaerCodeSerializer(serializers.Serializer):
   master_ids = serializers.ListField()

class DeleteRequirementsSerializer(serializers.Serializer):
   id = serializers.ListField()


class MasterCodeSerializer(serializers.Serializer):
    files = serializers.FileField()

class RequirementImportSerializer(serializers.Serializer):
    files = serializers.FileField()
class DeleteAssetSerializer(serializers.Serializer):
   id = serializers.ListField()
class DeleteCountryRequirementSerializer(serializers.Serializer):
   id = serializers.ListField()
   country = serializers.CharField(max_length=4)

class BlendDeleteSerializer(serializers.Serializer):
    id = serializers.ListField()
class IngredientDeleteSerializer(serializers.Serializer):
    id = serializers.ListField()

class DeleteLegalNameUpdateSerializer(serializers.Serializer):
    id = serializers.ListField()
class BlendImportExcelSerializer(serializers.Serializer):
    files = serializers.FileField()

class LegalNameImportExcelSerializer(serializers.Serializer):
    files = serializers.FileField()
class UpdateUserSerializer(serializers.Serializer):
    firstname = serializers.CharField(max_length=100)
    lastname = serializers.CharField(max_length=100)
    username =serializers.CharField(max_length=100)

class ChatSerializer(serializers.Serializer):
    chat = serializers.CharField(max_length=1000)
    user = serializers.CharField(max_length=140)
    varient = serializers.CharField(max_length=100)

class DocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Attachment
        fields =['varient','attachment']
class SalesReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = SalesReport
        fields =['varient','file']
class ArtWorkSerializer(serializers.ModelSerializer):
    class Meta:
        model = ArtWorks
        fields = ['varient','item','job','attachment']
class BlendRequirementSerializer(serializers.Serializer):
    requirement = serializers.CharField(max_length=1000,allow_blank=False)
    type = serializers.CharField(max_length=100,allow_blank=False)
    value = serializers.CharField(max_length=100,allow_blank=False)
    blend = serializers.CharField(max_length=200,allow_blank=False)
    country = serializers.ListField(allow_empty=False)
    category = serializers.CharField(allow_blank=False)

class ItemRequirementSerializer(serializers.Serializer):
    requirement = serializers.CharField(max_length=1000,allow_blank=False)
    type = serializers.CharField(max_length=100,allow_blank=False)
    value = serializers.CharField(max_length=100,allow_blank=False)
    item = serializers.CharField(max_length=200,allow_blank=False)
    country = serializers.ListField(allow_empty=False)

class ItemNoSerializers(serializers.Serializer):
    item = serializers.IntegerField(allow_null=False)
    blend_name = ListField(allow_empty=False)
    category = serializers.CharField(max_length=100,allow_blank=False)
    noTeabag = serializers.CharField(allow_blank=True)

def validate_registration(value):
    max_length = 9  # Maximum length allowed for the registration field

    if value is None:
        raise serializers.ValidationError("Registration field cannot be null.")

    max_length = 9  # Maximum length allowed for the registration field

    if len(str(value)) > max_length:
        raise serializers.ValidationError("Registration length exceeds the maximum allowed.")

    return value

class GroupedTranslation(serializers.Serializer):
    name = serializers.CharField(allow_blank=False)
    id = serializers.CharField(allow_blank=False)
class RegistrationNoSerializer(serializers.Serializer):
    item = serializers.CharField(allow_blank=False)
    country = serializers.CharField(allow_blank=False)
    registration = serializers.IntegerField(validators=[validate_registration])
