$(document).ready(function () {
    $("#top_back").click(function () {

        var pathName = window.location.pathname;
        var match = pathName.match(/\/(\w+)\/\d+\/\d+/);
        var backURL = "";

        if (match) {
            if (match[1] == 'cart')
                backURL = 'product'
            else if (match[1] == 'payment')
                backURL = 'cart'
            else if (match[1] == 'qr' || match[1] == 'funding' || match[1] == 'verification' || match[1] == 'verification_success' || match[1] == 'verification_fail')
                backURL = 'payment'
            else if (match[1] == 'purchase_success')
                backURL = 'product'
            else if (match[1] == 'purchase_fail')
                backURL = 'verification'
        }

        var lang_id = $("#language_id").val();
        var product_id = $("#product_id").val();

        if (backURL != "payment")
            window.location.replace('/'+ backURL +'/' + product_id + '/' + lang_id);
        else
            window.location.replace('/'+ backURL +'/' + product_id + '/' + lang_id + '/0/0');
    })

    const images = document.querySelectorAll('img');
        images.forEach(img => {
            img.setAttribute('draggable', 'false');
        });
});