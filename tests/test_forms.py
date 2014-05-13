from core_serializers import BasicObject, fields, renderers, serializers
import copy


def strip(text):
    """
    Strip leading and trailing whitespace from every line in a string, and
    ignore blank lines. Used for neater whitespace-ignoring comparisons.
    """
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
            <input class="form-control" name="field_name">
        </div>
    """
    populated_html = """
        <div class="form-group">
            <label>Text input</label>
            <input class="form-control" name="field_name" value="example">
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
            <textarea class="form-control" name="field_name" rows=5>
        </div>
    """
    populated_html = """
        <div class="form-group">
            <label>Textarea</label>
            <textarea class="form-control" name="field_name" value="longer example text" rows=5>
        </div>
    """


class TestSelect(HTMLFormsBaseCase):
    base_field = fields.ChoiceField(
        choices=[(1, 'Option one'), (2, 'Option two')],
        initial=2
    )
    populated_value = 1
    empty_html = """
        <select class="form-control" name="field_name">
          <option value="1" >Option one</option>
          <option value="2" selected>Option two</option>
        </select>
    """
    populated_html = """
        <select class="form-control" name="field_name">
          <option value="1" selected>Option one</option>
          <option value="2" >Option two</option>
        </select>
    """


class TestMultipleSelect(HTMLFormsBaseCase):
    base_field = fields.MultipleChoiceField(
        choices=[(1, 'Option one'), (2, 'Option two')],
        initial=[2]
    )
    populated_value = [1]
    empty_html = """
        <select multiple class="form-control" name="field_name">
          <option value="1" >Option one</option>
          <option value="2" selected>Option two</option>
        </select>
    """
    populated_html = """
        <select multiple class="form-control" name="field_name">
          <option value="1" selected>Option one</option>
          <option value="2" >Option two</option>
        </select>
    """


class TestRadio(HTMLFormsBaseCase):
    base_field = fields.ChoiceField(
        choices=[(1, 'Option one'), (2, 'Option two')],
        initial=2,
        style={'type': 'radio'}
    )
    populated_value = 1
    empty_html = """
        <div class="radio">
            <label >
                <input type="radio" name="field_name" value="1" >
                Option one
            </label>
        </div>
        <div class="radio">
            <label >
                <input type="radio" name="field_name" value="2" checked>
                Option two
            </label>
        </div>
    """
    populated_html = """
        <div class="radio">
            <label >
                <input type="radio" name="field_name" value="1" checked>
                Option one
            </label>
        </div>
        <div class="radio">
            <label >
                <input type="radio" name="field_name" value="2" >
                Option two
            </label>
        </div>
    """