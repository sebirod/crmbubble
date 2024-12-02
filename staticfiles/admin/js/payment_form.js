(function($) {
    $(function() {
        var $paymentMethod = $('#id_payment_method');
        var $cardFields = $('#id_card_number, #id_card_expiry, #id_card_ccv').closest('.form-row');
        var $bankFields = $('#id_bank_account_holder, #id_bank_account_iban').closest('.form-row');

        function toggleFields() {
            var method = $paymentMethod.val();
            $cardFields.toggle(method === 'CARD');
            $bankFields.toggle(method === 'BANK');
        }

        $paymentMethod.on('change', toggleFields);
        toggleFields();
    });
})(django.jQuery);