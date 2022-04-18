from django import template

register = template.Library()

@register.filter(name='times') 
def times(number):
    return range(number)

@register.filter(name='dict_key')
def dict_key(d, key):
    return d[key]

@register.filter(name='remove_one')
def remove_one(the_list, to_remove):
    the_list.remove(to_remove)
    return the_list
