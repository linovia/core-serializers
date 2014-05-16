from core_serializers import fields, renderers, serializers
from core_serializers.utils import BasicObject
import copy
import re


def strip(text):
    """
    Strip leading and trailing whitespace from every line in a string, and
    ignore blank lines. Used for neater whitespace-ignoring comparisons.
    """
    text = re.sub(' +', ' ', text)
    text = re.sub(' >', '>', text)
    lines = text.strip().splitlines()
    return '\n'.join([line.strip() for line in lines if line.strip()])


class HTMLFormsBaseCase:
    def setup(self):
        class TestSerializer(serializers.Serializer):
            field_name = copy.copy(self.base_field)
        self.serializer = TestSerializer()
        self.renderer = renderers.FormRenderer()

    def test_empty_form(self):
        empty = self.serializer.serialize()
        output = self.renderer.render(empty)
        assert strip(output) == strip(self.empty_html)

    def test_populated_form(self):
        obj = BasicObject(field_name=self.populated_value)
        populated = self.serializer.serialize(obj)
        output = self.renderer.render(populated)
        assert strip(output) == strip(self.populated_html)


class TestInput(HTMLFormsBaseCase):
    base_field = fields.CharField(
        label='Text input'
    )
    populated_value = 'example'
    empty_html = """
        <div class="form-group">
            <label>Text input</label>
            <input type="text" class="form-control" name="field_name">
        </div>
    """
    populated_html = """
        <div class="form-group">
            <label>Text input</label>
            <input type="text" class="form-control" name="field_name" value="example">
        </div>
    """


class TestInteger(HTMLFormsBaseCase):
    base_field = fields.IntegerField(
        label='Text input'
    )
    populated_value = 'example'
    empty_html = """
        <div class="form-group">
            <label>Text input</label>
            <input type="number" class="form-control" name="field_name">
        </div>
    """
    populated_html = """
        <div class="form-group">
            <label>Text input</label>
            <input type="number" class="form-control" name="field_name" value="example">
        </div>
    """


class TestTextArea(HTMLFormsBaseCase):
    base_field = fields.CharField(
        label='Textarea',
        style={'type': 'textarea', 'rows': 5}
    )
    populated_value = 'longer example text'
    empty_html = """
        <div class="form-group">
            <label>Textarea</label>
            <textarea class="form-control" name="field_name" rows="5"></textarea>
        </div>
    """
    populated_html = """
        <div class="form-group">
            <label>Textarea</label>
            <textarea class="form-control" name="field_name" rows="5">longer example text</textarea>
        </div>
    """


class TestCheckbox(HTMLFormsBaseCase):
    base_field = fields.BooleanField(
        label='Boolean field',
    )
    populated_value = True
    empty_html = """
        <div class="checkbox">
            <label>
                <input type="checkbox" name="field_name" value="true" >
                Boolean field
            </label>
        </div>
    """
    populated_html = """
        <div class="checkbox">
            <label>
                <input type="checkbox" name="field_name" value="true" checked>
                Boolean field
            </label>
        </div>
    """


class TestSelect(HTMLFormsBaseCase):
    base_field = fields.ChoiceField(
        choices=[(1, 'Option one'), (2, 'Option two')],
        initial=2
    )
    populated_value = 1
    empty_html = """
        <div class="form-group">
            <label>Field name</label>
            <select class="form-control" name="field_name">
                <option value="1" >Option one</option>
                <option value="2" selected>Option two</option>
            </select>
        </div>
    """
    populated_html = """
        <div class="form-group">
            <label>Field name</label>
            <select class="form-control" name="field_name">
              <option value="1" selected>Option one</option>
              <option value="2" >Option two</option>
            </select>
        </div>
    """


class TestMultipleSelect(HTMLFormsBaseCase):
    base_field = fields.MultipleChoiceField(
        choices=[(1, 'Option one'), (2, 'Option two')],
        initial=[2]
    )
    populated_value = [1, 2]
    empty_html = """
        <div class="form-group">
            <label>Field name</label>
            <select multiple class="form-control" name="field_name">
              <option value="1" >Option one</option>
              <option value="2" selected>Option two</option>
            </select>
        </div>
    """
    populated_html = """
        <div class="form-group">
            <label>Field name</label>
            <select multiple class="form-control" name="field_name">
                <option value="1" selected>Option one</option>
                <option value="2" selected>Option two</option>
            </select>
        </div>
    """


class TestRadio(HTMLFormsBaseCase):
    base_field = fields.ChoiceField(
        choices=[(1, 'Option one'), (2, 'Option two')],
        initial=2,
        style={'type': 'radio'}
    )
    populated_value = 1
    empty_html = """
        <div class="form-group">
            <label>Field name</label>
            <div class="radio">
                <label>
                    <input type="radio" name="field_name" value="1">
                    Option one
                </label>
            </div>
            <div class="radio">
                <label >
                    <input type="radio" name="field_name" value="2" checked>
                    Option two
                </label>
            </div>
        </div>
    """
    populated_html = """
        <div class="form-group">
            <label>Field name</label>
            <div class="radio">
                <label>
                    <input type="radio" name="field_name" value="1" checked>
                    Option one
                </label>
            </div>
            <div class="radio">
                <label>
                    <input type="radio" name="field_name" value="2">
                    Option two
                </label>
            </div>
        </div>
    """


class TestMultipleCheckbox(HTMLFormsBaseCase):
    base_field = fields.MultipleChoiceField(
        choices=[(1, 'Option one'), (2, 'Option two')],
        initial=[2],
        style={'type': 'checkbox'}
    )
    populated_value = [1, 2]
    empty_html = """
        <div class="form-group">
            <label>Field name</label>
            <div class="checkbox">
                <label>
                    <input type="checkbox" name="field_name" value="1" >
                    Option one
                </label>
            </div>
            <div class="checkbox">
                <label >
                    <input type="checkbox" name="field_name" value="2" checked>
                    Option two
                </label>
            </div>
        </div>
    """
    populated_html = """
        <div class="form-group">
            <label>Field name</label>
            <div class="checkbox">
                <label>
                    <input type="checkbox" name="field_name" value="1" checked>
                    Option one
                </label>
            </div>
            <div class="checkbox">
                <label>
                    <input type="checkbox" name="field_name" value="2" checked>
                    Option two
                </label>
            </div>
        </div>
    """