(function () {
    'use strict';

    var state = {
        currentInput: '0',
        operand1: null,
        operator: null,
        waitingForSecond: false,
        expression: ''
    };

    var history = [];

    function updateDisplay() {
        AJS.$('#calc-current').text(state.currentInput);
        AJS.$('#calc-expression').text(state.expression || ' ');
    }

    function formatNumber(num) {
        var str = String(num);
        if (str.indexOf('.') !== -1) {
            str = str.replace(/\.?0+$/, '');
        }
        return str || '0';
    }

    function appendHistory(entry) {
        history.unshift(entry);
        if (history.length > 5) {
            history.pop();
        }
        var $list = AJS.$('#calc-history-list');
        $list.empty();
        AJS.$.each(history, function (i, item) {
            $list.append('<li>' + item + '</li>');
        });
    }

    function handleNumber(value) {
        if (state.waitingForSecond) {
            state.currentInput = value;
            state.waitingForSecond = false;
        } else {
            state.currentInput = state.currentInput === '0' ? value : state.currentInput + value;
        }
        updateDisplay();
    }

    function handleOperator(value) {
        state.operand1 = state.currentInput;
        state.operator = value;
        state.expression = state.currentInput + ' ' + value;
        state.waitingForSecond = true;
        updateDisplay();
    }

    function handleClear() {
        state.currentInput = '0';
        state.operand1 = null;
        state.operator = null;
        state.waitingForSecond = false;
        state.expression = '';
        updateDisplay();
    }

    function handleDecimal() {
        if (state.waitingForSecond) {
            state.currentInput = '0.';
            state.waitingForSecond = false;
        } else if (state.currentInput.indexOf('.') === -1) {
            state.currentInput += '.';
        }
        updateDisplay();
    }

    function handleSign() {
        if (state.currentInput !== '0') {
            state.currentInput = state.currentInput.charAt(0) === '-'
                ? state.currentInput.slice(1)
                : '-' + state.currentInput;
            updateDisplay();
        }
    }

    function handlePercent() {
        var val = parseFloat(state.currentInput);
        if (!isNaN(val)) {
            state.currentInput = formatNumber(val / 100);
            updateDisplay();
        }
    }

    function handleEquals() {
        if (state.operand1 === null || state.operator === null) {
            return;
        }

        var operand2 = state.currentInput;
        var expression = state.operand1 + ' ' + state.operator + ' ' + operand2;

        AJS.$.ajax({
            url: AJS.contextPath() + '/rest/calculator/1.0/calculate',
            type: 'POST',
            contentType: 'application/json',
            data: JSON.stringify({
                operand1: state.operand1,
                operator: state.operator,
                operand2: operand2
            }),
            success: function (response) {
                if (response.error) {
                    state.currentInput = 'Error';
                    state.expression = response.error;
                } else {
                    var resultStr = formatNumber(response.result);
                    appendHistory(expression + ' = ' + resultStr);
                    state.currentInput = resultStr;
                    state.expression = expression + ' =';
                }
                state.operand1 = null;
                state.operator = null;
                state.waitingForSecond = false;
                updateDisplay();
            },
            error: function () {
                state.currentInput = 'Error';
                state.expression = 'Request failed';
                state.operand1 = null;
                state.operator = null;
                state.waitingForSecond = false;
                updateDisplay();
            }
        });
    }

    AJS.$(document).ready(function () {
        updateDisplay();

        AJS.$('.calc-grid').on('click', '.calc-btn', function () {
            var $btn = AJS.$(this);
            var action = $btn.data('action');
            var value = $btn.data('value');

            switch (action) {
                case 'number':   handleNumber(String(value)); break;
                case 'operator': handleOperator(value); break;
                case 'clear':    handleClear(); break;
                case 'decimal':  handleDecimal(); break;
                case 'sign':     handleSign(); break;
                case 'percent':  handlePercent(); break;
                case 'equals':   handleEquals(); break;
            }
        });
    });
}());
