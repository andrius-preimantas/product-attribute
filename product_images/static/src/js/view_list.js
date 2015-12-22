openerp.product_images = function(instance) {

    var QWeb = instance.web.qweb;
    var _t = instance.web._t;

    instance.web.list.columns.add('field.image','instance.web.list.FieldBinaryImage');
    instance.web.list.FieldBinaryImage = instance.web.list.Column.extend({
        /**
         * Return a image to the binary field of specified as widget image
         *
         * @private
         */
        _format: function (row_data, options) {
            var placeholder = "/web/static/src/img/placeholder.png";
            var value = row_data[this.id].value;
            var img_url = placeholder;

            if (value && value.substr(0, 10).indexOf(' ') == -1) {
            /* Data inline */
            /* FIXME: can we get the mimetype from the data? */
                img_url = "data:image/png;base64," + value;
            } else {
            /* Data by URI (presumably slow) */
                img_url = instance.session.url('/web/binary/image', {model: options.model, field: this.id, id: options.id});
            }
            return _.template('<image src="<%-src%>" height="65px"/>', {
                src: img_url,
            });
        }
    });
}