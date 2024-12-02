document.addEventListener('DOMContentLoaded', function() {
    const paymentMethodField = document.getElementById('id_payment_method');
    const cardFields = ['id_card_number', 'id_card_expiry', 'id_card_cvc'];
    const bankFields = ['id_bank_account', 'id_bank_name', 'id_bank_routing'];

    function updateFormFields() {
        const selectedPaymentMethod = paymentMethodField.value;

        cardFields.forEach(function(field) {
            const element = document.getElementById(field).closest('.form-row');
            if (selectedPaymentMethod === 'Credit Card') {
                element.style.display = 'block';
            } else {
                element.style.display = 'none';
            }
        });

        bankFields.forEach(function(field) {
            const element = document.getElementById(field).closest('.form-row');
            if (selectedPaymentMethod === 'Bank Account') {
                element.style.display = 'block';
            } else {
                element.style.display = 'none';
            }
        });
    }

    paymentMethodField.addEventListener('change', updateFormFields);
    updateFormFields();  // Inicializa con el estado correcto
});