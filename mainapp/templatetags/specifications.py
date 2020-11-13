from django import template
from django.utils.safestring import mark_safe
from mainapp.models import Smartphone

register = template.Library()

TABLE_HEAD = '''
                <table class="table table-dark">
                    <tbody>
             '''

TABLE_TAIL = '''
                    </tbody>
                </table>
             '''

TABLE_CONTENT = '''
                    <tr>
                        <td>{name}</td>
                        <td>{value}</td>
                    </tr>
                '''

PRODUCT_SPEC = {
    "notebook": {
        "Անկյունագիծ": "diagonal",
        "Ցուցադրման տիպ": "display_type",
        "Պրոցեսորի մաքրություն": "processor_freq",
        "Օպերատիվ հիշողություն": "ram",
        "Վիդեոքարտ": "video",
        "Մարտկոցի աշխատանքի ժամանակ": "time_without_charge"
    },
    "smartphone": {
        "Անկյունագիծ": "diagonal",
        "Ցուցադրման տիպ": "display_type",
        "Էկրանի ընդլայնում": "resolution",
        "Մարտկոցի ծավալ": "accum_volume",
        "Օպերատիվ հիշողություն": "ram",
        "Ներդրված SD քարտի հիշողության ծավալ": "sd",
        "Մեծագույն ներդրման հիշողության ծավալ": "sd_volume_max",
        "Ետևի տեսախցիկ": "main_cam_mp",
        "Առջևի տեսախցիկ": "frontal_cam_mp"
    }
}


def get_product_spec(product, model_name):
    table_content = ""
    for name, value in PRODUCT_SPEC[model_name].items():
        table_content += TABLE_CONTENT.format(name=name, value=getattr(product, value))
    return table_content


@register.filter
def product_spec(product):
    model_name = product.__class__._meta.model_name
    if isinstance(product, Smartphone):
        if not product.sd:
            PRODUCT_SPEC["smartphone"].pop("Մեծագույն ներդրման հիշողության ծավալ")
        else:
            PRODUCT_SPEC["smartphone"]["Մեծագույն ներդրման հիշողության ծավալ"] = "sd_volume_max"
    return mark_safe(TABLE_HEAD + get_product_spec(product, model_name) + TABLE_TAIL)
