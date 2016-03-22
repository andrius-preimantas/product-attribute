# -*- coding: utf-8 -*-
# This file is part of OpenERP. The COPYRIGHT file at the top level of
# this module contains the full copyright notices and license terms.
from openerp import models, fields, api, tools
import PIL
import cStringIO
import base64


class ProductProduct(models.Model):
    _inherit = "product.product"

    @api.multi
    @api.depends('image_ids', 'image_ids.file')
    def _get_variant_images(self):
        for each in self:
            res = {'image': None, 'image_small': None, 'image_medium': None}
            if self.env.context.get('bin_size'):
                res['image'] = each.image_variant
                res['image_small'] = each.image_variant
                res['image_medium'] = each.image_variant
            else:
                res = tools.image_get_resized_images(
                    each.image_variant, return_big=True,
                    avoid_resize_medium=True)
            each.image = res['image']
            each.image_medium = res['image_medium']
            each.image_small = res['image_small']

    @api.multi
    def set_variant_image(self, field_to_read):
        for each in self:
            image_data = getattr(each, field_to_read)
            image = tools.image_resize_image_big(image_data)
            if each.product_tmpl_id.image:
                each.image_variant = image
            else:
                each.product_tmpl_id.image = image

    @api.multi
    def _set_variant_image(self):
        self.set_variant_image('image')

    @api.multi
    def _set_variant_image_small(self):
        self.set_variant_image('image_small')

    @api.multi
    def _set_variant_image_medium(self):
        self.set_variant_image('image_medium')

    @api.multi
    def _get_image_variant(self):
        for each in self:
            each.image_variant = each.product_image

    @api.multi
    def _set_image_variant(self):
        for each in self:
            default_image_name = each.image_name or (
                'Main image.' + each.guess_image_type(each.image_variant))
            main_image = each.get_main_image()
            if main_image:
                main_image.file = each.image_variant
            else:
                data = {'file': each.image_variant, 'name': default_image_name}
                each.write({'image_ids': [(0, 0, data)]})
                each.image_variant = each.product_image

    image_variant = fields.Binary(
        string="Variant Image", compute="_get_image_variant",
        inverse="_set_image_variant", store=True,
        help="This field holds the image used as image for the product "
        "variant, limited to 1024x1024px.")
    image = fields.Binary(
        string="Big-sized image", compute='_get_variant_images',
        inverse='_set_variant_image', store=True,
        help="Image of the product variant (Big-sized image of product "
        "template if false). It is automatically resized as a 1024x1024px "
        "image, with aspect ratio preserved.")
    image_small = fields.Binary(
        string="Small-sized image", compute='_get_variant_images',
        inverse='_set_variant_image_small', store=True,
        help="Image of the product variant (Small-sized image of product "
        "template if false).")
    image_medium = fields.Binary(
        compute='_get_variant_images', string="Medium-sized image",
        inverse='_set_variant_image_medium', store=True,
        help="Image of the product variant (Medium-sized image of product "
        "template if false).")


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    @api.multi
    @api.depends('product_variant_ids.image_ids',
                 'product_variant_ids.image_ids.file')
    def _get_images(self):
        for each in self:
            res = {'image': None, 'image_small': None, 'image_medium': None}
            if each.image_ids:
                res = tools.image_get_resized_images(
                    each.image_ids[0].file, avoid_resize_medium=True)
                res['image'] = each.image_ids[0].file

            each.image = res['image']
            each.image_medium = res['image_medium']
            each.image_small = res['image_small']

    @api.model
    def guess_image_type(self, binary_data):
        string_data = base64.b64decode(binary_data)
        image = PIL.Image.open(cStringIO.StringIO(string_data))
        return image.format

    @api.multi
    def _set_image(self):
        for each in self:
            image = each.product_variant_ids[0].get_main_image()
            default_image_name = each.image_name or (
                'Main image.' + self.guess_image_type(each.image))
            if image:
                image.name = default_image_name
                image.file = each.image
            else:
                image_ids = [
                    (0, 0, {'name': default_image_name, 'file': each.image})
                ]
                each.product_variant_ids[0].write(
                    {'image_ids': image_ids})

    @api.multi
    def _set_image_small(self):
        for each in self:
            each.image = tools.image_resize_image_big(each.image_small)

    @api.multi
    def _set_image_medium(self):
        for each in self:
            each.image = tools.image_resize_image_big(each.image_medium)

    image_name = fields.Char()
    image = fields.Binary(
        compute='_get_images', inverse='_set_image', store=True,
        help="This field holds the image used as image for the product, "
        "limited to 1024x1024px.")
    image_small = fields.Binary(
        compute='_get_images', inverse='_set_image_small',
        string="Small-sized image", store=True,
        help="Small-sized image of the product. It is automatically "
             "resized as a 64x64px image, with aspect ratio preserved. "
             "Use this field anywhere a small image is required.")
    image_medium = fields.Binary(
        compute='_get_images', inverse='_set_image_medium',
        string="Medium-sized image", store=True,
        help="Medium-sized image of the product. It is automatically "
             "resized as a 128x128px image, with aspect ratio preserved, "
             "only when the image exceeds one of those sizes. Use this field "
             "in form views or some kanban views.")
