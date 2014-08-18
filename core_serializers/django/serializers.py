
from django.db import models
from django.forms import widgets
from django.utils.six import add_metaclass

# from core_serializers.fields import *  # NOQA
from .fields import *

from core_serializers import serializers
from collections import OrderedDict


class ModelSerializerOptions(object):
    """
    Meta class options for ModelSerializer
    """
    def __init__(self, meta):
        self.fields = getattr(meta, 'fields', ())
        self.model = getattr(meta, 'model', None)
        # self.depth = getattr(meta, 'depth', 0)
        # self.read_only_fields = getattr(meta, 'read_only_fields', ())
        # self.write_only_fields = getattr(meta, 'write_only_fields', ())


class ModelSerializerMetaclass(serializers.SerializerMetaclass):
    def __new__(self, name, bases, attrs):
        # Skip the field construction if this is applied on the base class
        if name != 'ModelSerializer':
            introspection = ModelIntrospection(self, name, bases, attrs)
            attrs.update(introspection._get_fields())
        cls = super(ModelSerializerMetaclass, self).__new__(self, name, bases, attrs)
        return cls


class ModelIntrospection(object):

    def __init__(self, metacls, name, bases, attrs):
        self.metacls = metacls
        self.name = name
        self.bases = bases
        self.attrs = attrs

    def get_from_bases(self, attr_name):
        '''
        Helper to browse the class history
        Required because we don't have yet a fully working class
        '''
        try:
            return self.attrs[attr_name]
        except KeyError:
            pass

        for base in self.bases:
            try:
                return getattr(base, attr_name)
            except AttributeError:
                pass
        return None


    #
    # Extracts the fields from the model
    #

    def get_default_fields(self):
        """
        Return all the fields that should be serialized for the model.
        """
        meta = self.get_from_bases('Meta')
        model = getattr(meta, 'model', None)
        assert model is not None, \
                "Serializer class '%s' is missing 'model' Meta option (%s)" % (model.__class__.__name__, self.bases)

        ret = OrderedDict()

        # TODO: Rework the primary key field detection
        # ret.update(self.metacls.get_pk(opts))

        # Get the meta fields or fallback on all the model's fields
        fields = getattr(meta, 'fields',
            [f.name for f in model._meta.concrete_fields])

        # Create the associated dictionnary
        for field_name in fields:
            model_field = model._meta.get_field_by_name(field_name)[0]
            field = self.get_field(model_field)

            if field:
                ret[model_field.name] = field

        return ret

    def _get_fields(self): #, bases, attrs):
        """
        Returns the complete set of fields for the object as a dict.

        This will be the set of any explicitly declared fields,
        plus the set of fields returned by get_default_fields().
        """
        base = self.metacls._get_fields(self.bases, self.attrs)
        ret = OrderedDict()

        # Add in the default fields
        default_fields = self.get_default_fields()
        for key, val in default_fields.items():
            if key not in ret:
                ret[key] = val

        # If 'fields' is specified, use those fields, in that order.
        fields = getattr(self.attrs['Meta'], 'fields', [])
        if fields:
            assert isinstance(fields, (list, tuple)), '`fields` must be a list or tuple'
            new = OrderedDict()
            for key in fields:
                new[key] = ret[key]
            ret = new

        # Reintegrate the explicit fields
        ret.update(base)

        # TODO: check if we still need to initialize the fields
        # for key, field in ret.items():
        #     field.initialize(parent=self, field_name=key)

        return ret

    #
    # PK
    #

    def get_pk(self, opts):
        """
        Get the real pk for the given class options
        """
        ret = {}

        # Deal with adding the primary key field
        pk_field = opts.pk
        while pk_field.rel and pk_field.rel.parent_link:
            # If model is a child via multitable inheritance, use parent's pk
            pk_field = pk_field.rel.to._meta.pk

        field = self.get_pk_field(pk_field)

        if field:
            ret[pk_field.name] = field

        return ret

    def get_pk_field(self, model_field):
        """
        Returns a default instance of the pk field.
        """
        return self.get_field(model_field)

    #
    # Field creation
    #
    def get_field(self, model_field):
        """
        Creates a default instance of a basic non-relational field.
        """
        kwargs = {}

        if model_field.null or model_field.blank:
            kwargs['required'] = False

        if isinstance(model_field, models.AutoField) or not model_field.editable:
            kwargs['read_only'] = True

        if model_field.has_default():
            kwargs['default'] = model_field.get_default()

        if issubclass(model_field.__class__, models.TextField):
            kwargs['widget'] = widgets.Textarea

        if model_field.verbose_name is not None:
            kwargs['label'] = model_field.verbose_name

        if model_field.help_text is not None:
            kwargs['help_text'] = model_field.help_text

        # TODO: TypedChoiceField?
        if model_field.flatchoices:  # This ModelField contains choices
            kwargs['choices'] = model_field.flatchoices
            if model_field.null:
                kwargs['empty'] = None
            return ChoiceField(**kwargs)

        # put this below the ChoiceField because min_value isn't a valid initializer
        if issubclass(model_field.__class__, models.PositiveIntegerField) or\
                issubclass(model_field.__class__, models.PositiveSmallIntegerField):
            kwargs['min_value'] = 0

        attribute_dict = {
            models.CharField: ['max_length'],
            models.CommaSeparatedIntegerField: ['max_length'],
            models.DecimalField: ['max_digits', 'decimal_places'],
            models.EmailField: ['max_length'],
            models.FileField: ['max_length'],
            models.ImageField: ['max_length'],
            models.SlugField: ['max_length'],
            models.URLField: ['max_length'],
        }

        if model_field.__class__ in attribute_dict:
            attributes = attribute_dict[model_field.__class__]
            for attribute in attributes:
                kwargs.update({attribute: getattr(model_field, attribute)})

        try:
            field_mapping = self.get_from_bases('field_mapping')
            return field_mapping[model_field.__class__](**kwargs)
        except KeyError:
            return Field(model_field=model_field, **kwargs)


@add_metaclass(ModelSerializerMetaclass)
class ModelSerializer(serializers.Serializer):
    _options_class = ModelSerializerOptions

    field_mapping = {
        models.AutoField: IntegerField,
        # models.FloatField: FloatField,
        models.IntegerField: IntegerField,
        models.PositiveIntegerField: IntegerField,
        models.SmallIntegerField: IntegerField,
        models.PositiveSmallIntegerField: IntegerField,
        # models.DateTimeField: DateTimeField,
        # models.DateField: DateField,
        # models.TimeField: TimeField,
        # models.DecimalField: DecimalField,
        # models.EmailField: EmailField,
        models.CharField: CharField,
        # models.URLField: URLField,
        # models.SlugField: SlugField,
        models.TextField: CharField,
        models.CommaSeparatedIntegerField: CharField,
        models.BooleanField: BooleanField,
        models.NullBooleanField: BooleanField,
        # models.FileField: FileField,
        # models.ImageField: ImageField,
    }

    class Meta(object):
        pass

    def __init__(self, *args, **kwargs):
        self.opts = self._options_class(self.Meta)
        # compat: Clean up some context from DRF 2.x
        # for item in ('many', 'context', 'partial', 'files', 'allow_add_remove'):
        #     kwargs.pop(item, None)
        super(ModelSerializer, self).__init__(*args, **kwargs)

    #
    # Regular serializer functions
    #

    # def to_primative(self, instance):
    #     """
    #     Object instance -> Dict of primitive datatypes.
    #     """
    #     ret = OrderedDict()
    #     fields = [field for field in self.fields.values() if not field.write_only]

    #     for field in fields:
    #         native_value = field.get_attribute(instance)
    #         ret[field.field_name] = field.to_primative(native_value)

    #     return ret


    def create(self, validated_data):
        return self.opts.model(**validated_data)

    def save(self, commit=True):
        instance = super(ModelSerializer, self).save()
        if commit:
            instance.save()
        return instance
