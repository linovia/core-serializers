from core_serializers import BasicObject, fields, renderers, serializers

empty_form = """
<div class="form-group">
    <label>Text input</label>
    <input class="form-control" id="charfield">
</div>
<div class="form-group">
    <label>Textarea</label>
    <textarea class="form-control" id="textfield" rows=5>
</div>""".strip()

populated_form = """
<div class="form-group">
    <label>Text input</label>
    <input class="form-control" id="charfield" value="example">
</div>
<div class="form-group">
    <label>Textarea</label>
    <textarea class="form-control" id="textfield" value="longer example text" rows=5>
</div>""".strip()


class TestForms:
    def setup(self):
        class TestSerializer(serializers.Serializer):
            charfield = fields.CharField(label='Text input')
            textfield = fields.CharField(label='Textarea',
                                         style={'type': 'textarea', 'rows': 5})

        self.serializer = TestSerializer()
        self.renderer = renderers.FormRenderer()

    def test_empty_form(self):
        empty = self.serializer.serialize()
        output = self.renderer.render(empty)
        assert output.strip() == empty_form

    def test_populated_form(self):
        obj = BasicObject(charfield='example', textfield='longer example text')
        empty = self.serializer.serialize(obj)
        output = self.renderer.render(empty)
        assert output.strip() == populated_form
