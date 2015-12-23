# -*- coding: utf-8 -*-
#########################################################################
# Copyright (C) 2009  Sharoon Thomas, Open Labs Business solutions      #
# Copyright (C) 2011 Akretion Sébastien BEAU sebastien.beau@akretion.com#
#                                                                       #
#This program is free software: you can redistribute it and/or modify   #
#it under the terms of the GNU General Public License as published by   #
#the Free Software Foundation, either version 3 of the License, or      #
#(at your option) any later version.                                    #
#                                                                       #
#This program is distributed in the hope that it will be useful,        #
#but WITHOUT ANY WARRANTY; without even the implied warranty of         #
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the          #
#GNU General Public License for more details.                           #
#                                                                       #
#You should have received a copy of the GNU General Public License      #
#along with this program.  If not, see <http://www.gnu.org/licenses/>.  #
#########################################################################
import os
import shutil
import logging
import base64
import urllib

from openerp import models, fields, api, exceptions


class ProductProduct(models.Model):
    _inherit = "product.product"

    @api.returns('self', lambda value: value.id)
    def copy(self, cr, uid, id, default=None, context=None):
        if not default:
            default = {}
        original = self.read(fields=['default_code', 'image_ids'])
        default.update({
            'image_ids': False,
        })
        local_media_repository = self.env[
            'res.company'].get_local_media_repository()
        if local_media_repository:
            if original['image_ids']:
                old_path = os.path.join(
                    local_media_repository, original['default_code'])
                if os.path.isdir(old_path):
                    try:
                        shutil.copytree(old_path, old_path + '-copy')
                    except:
                        logger = logging.getLogger('product_images_olbs')
                        logger.exception('error while trying to copy images '
                                         'from %s to %s',
                                         old_path,
                                         old_path + '.copy')

        return super(ProductProduct, self).copy(
            cr, uid, id, default, context=context)

    def get_main_image(self):
        self.ensure_one()
        return self.images_ids and self.image_ids[0] or False

    @api.depends('image_ids')
    def _get_main_image(self):
        for record in self:
            image = record.get_main_image()
            record.product_image = image and image.file or False

    image_ids = fields.One2many(
        'product.images', 'product_id', string="Product Images")
    product_image = fields.Binary(
        compute='_get_main_image', string="Main Image")

    @api.multi
    def write(self, vals):
        # there's no constrain on unique default code anymore
        local_media_repository = self.env[
            'res.company'].get_local_media_repository()
        images = self.mapped('image_ids')

        # when changing default code we need to move images in local repo
        if 'default_code' in vals and images and local_media_repository:
            if len(self) != 1:
                raise exceptions.Warning(
                    "Unable to set same Internal Reference code for multiple "
                    "products because Product images are named and saved "
                    "locally based on Product Code!")
            if vals['default_code'] != self.default_code:
                old_path = os.path.join(
                    local_media_repository, self.default_code)
                if os.path.isdir(old_path):
                    os.rename(old_path, os.path.join(local_media_repository,
                              vals['default_code']))

        return super(ProductProduct, self).write(vals)

    @api.multi
    def create_image_from_url(self, url, image_name=None):
        self.ensure_one()
        (filename, header) = urllib.urlretrieve(url)
        with open(filename, 'rb') as f:
            data = f.read()
        img = base64.encodestring(data)
        filename, extension = os.path.splitext(os.path.basename(url))
        data = {'name': image_name or filename,
                'extension': extension,
                'file': img,
                'product_id': self.id,
                }
        self.env['product.images'].create(data)
        return True


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    image_ids = fields.One2many(related='product_variant_ids.image_ids')
