# -*- coding: utf-8 -*-
# This file is part of OpenERP. The COPYRIGHT file at the top level of
# this module contains the full copyright notices and license terms.
from openerp import models, fields, api, tools, exceptions
import PIL
import cStringIO
import base64


class ProductProduct(models.Model):
    _inherit = "product.product"

    @api.multi
    @api.depends('image_ids', 'image_ids.file', 'image_ids.sequence')
    def _get_variant_images(self):
        for each in self:
            res = {'image': None, 'image_small': None, 'image_medium': None}
            image = each.product_image
            if self.env.context.get('bin_size'):
                res['image'] = image
                res['image_small'] = image
                res['image_medium'] = image
            else:
                res = tools.image_get_resized_images(
                    image, return_big=True, avoid_resize_medium=True)
            each.image = res['image']
            each.image_medium = res['image_medium']
            each.image_small = res['image_small']

    @api.multi
    def set_variant_image(self, field_to_read):
        for each in self:
            image_data = getattr(each, field_to_read)
            image = tools.image_resize_image_big(image_data)
            image_current = each.product_variant_ids[0].get_main_image()
            image_name = (
                (image_current and image_current.name) or
                each.image_name or
                'Main image.' + self.product_tmpl_id.guess_image_type(image)
            )
            if image_current:
                image_current.write({'file': image, 'name': image_name})
            else:
                each.product_variant_ids[0].write(
                    {'image_ids': [
                        (0, 0, {'name': image_name, 'file': image})
                    ]}
                )

    @api.multi
    def _set_variant_image(self):
        self.set_variant_image('image')

    @api.multi
    def _set_variant_image_small(self):
        self.set_variant_image('image_small')

    @api.multi
    def _set_variant_image_medium(self):
        self.set_variant_image('image_medium')

    image_variant = fields.Binary(
        related="product_tmpl_id.image", store=True,
        help="This field holds the image used as image for the product "
        "variant, limited to 1024x1024px.")
    image = fields.Binary(
        string="Big-sized image", compute='_get_variant_images',
        inverse='_set_variant_image',
        help="Image of the product variant (Big-sized image of product "
        "template if false). It is automatically resized as a 1024x1024px "
        "image, with aspect ratio preserved.")
    image_small = fields.Binary(
        string="Small-sized image", compute='_get_variant_images',
        inverse='_set_variant_image_small',
        help="Image of the product variant (Small-sized image of product "
        "template if false).")
    image_medium = fields.Binary(
        string="Medium-sized image", compute='_get_variant_images',
        inverse='_set_variant_image_medium',
        help="Image of the product variant (Medium-sized image of product "
        "template if false).")


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    @api.multi
    @api.depends('product_variant_ids.image_ids',
                 'product_variant_ids.image_ids.file',
                 'product_variant_ids.image_ids.sequence')
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
    def save_image(self, field_to_read):
        for each in self:
            image_data = getattr(each, field_to_read)
            image_current = each.product_variant_ids[0].get_main_image()
            if image_current and not image_data:
                raise exceptions.Warning(
                    "Unable to remove image. Please delete all images "
                    "from Images tab first.")
            image = tools.image_resize_image_big(image_data)
            image_name = (
                each.image_name or
                (image_current and image_current.name) or
                'Main image.' + self.guess_image_type(image)
            )
            if image_current:
                image_current.write({'file': image, 'name': image_name})
            else:
                each.product_variant_ids[0].write(
                    {'image_ids': [
                        (0, 0, {'name': image_name, 'file': image})
                    ]}
                )

    @api.multi
    def _set_image(self):
        self.save_image('image')

    @api.multi
    def _set_image_small(self):
        self.save_image('image_small')

    @api.multi
    def _set_image_medium(self):
        self.save_image('image_medium')

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
