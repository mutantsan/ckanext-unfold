ckan.module("unfold-init-jstree", function ($, _) {
    "use strict";
    return {
        options: {
            data: null,
        },

        initialize: function () {
            $(this.el).jstree({
                'core': {
                    'data': this.options.data
                },
                "plugins": [
                    "search"
                ]
            });
        },
    };
});
