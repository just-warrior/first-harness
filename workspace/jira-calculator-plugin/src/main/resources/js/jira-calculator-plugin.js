(function () {
    'use strict';

    var state = {
        currentInput: '0',
        prevInput: null,
        operator: null,
        waitingForSecond: false
    };

    var history = [];
    var MAX_HISTORY = 5;

    function updateDisplay(value) {
        var $display = AJS.$('#calc-display');
        $display.text(value);
        $display.removeClass('calc-display-error');
    }

    function showError(msg) {
        var $display = AJS.$('#calc-display');
        $display.text(msg);
        $display.addClass('calc-display-error');
    }

    function resetState() {
        state.currentInput = '0';
        state.prevInput = null;
        state.operator = null;
        state.waitingForSecond = false;
        updateDisplay('0');
    }

    function addHistory(expression) {
        history.unshift(expression);
        if (history.length > MAX_HISTORY) {
            history.pop();
        }
        var $list = AJS.$('#calc-history-list');
        $list.empty();
        AJS.$.each(history, function (i, expr) {
            $list.append(AJS.$('<li>').text(expr));
        });
    }

    function handleNumber(value) {
        if (state.waitingForSecond) {
            state.currentInput = value;
            state.waitingForSecond = false;
        } else {
            state.currentInput = state.currentInput === '0'
                ? value
                : state.currentInput + value;
        }
        updateDisplay(state.currentInput);
    }

    function handleDecimal() {
        if (state.waitingForSecond) {
            state.currentInput = '0.';
            state.waitingForSecond = false;
            updateDisplay(state.currentInput);
            return;
        }
        if (state.currentInput.indexOf('.') === -1) {
            state.currentInput += '.';
            updateDisplay(state.currentInput);
        }
    }

    function handleOperator(op) {
        state.prevInput = state.currentInput;
        state.operator = op;
        state.waitingForSecond = true;
        updateDisplay(state.currentInput + ' ' + op);
    }

    function handleEquals() {
        if (state.prevInput === null || state.operator === null) {
            return;
        }

        var operand1 = state.prevInput;
        var operand2 = state.currentInput;
        var operator = state.operator;

        AJS.$.ajax({
            url: AJS.contextPath() + '/rest/calculator/1.0/calculate',
            type: 'POST',
            contentType: 'application/json',
            dataType: 'json',
            data: JSON.stringify({
                operand1: operand1,
                operator: operator,
                operand2: operand2
            }),
            success: function (data) {
                var resultStr = String(data.result);
                updateDisplay(resultStr);
                addHistory(data.expression);
                state.currentInput = resultStr;
                state.prevInput = null;
                state.operator = null;
                state.waitingForSecond = false;
            },
            error: function (xhr) {
                var msg = 'Error';
                try {
                    var body = JSON.parse(xhr.responseText);
                    if (body && body.error) {
                        msg = body.error;
                    }
                } catch (e) { /* ignore */ }
                showError(msg);
                state.prevInput = null;
                state.operator = null;
                state.currentInput = '0';
                state.waitingForSecond = false;
            }
        });
    }

    AJS.$(function () {
        AJS.$('.calc-grid').on('click', '.calc-btn', function (e) {
            var $btn = AJS.$(this);
            var action = $btn.data('action');
            var value = $btn.data('value');

            switch (action) {
                case 'number':
                    handleNumber(String(value));
                    break;
                case 'operator':
                    handleOperator(String(value));
                    break;
                case 'decimal':
                    handleDecimal();
                    break;
                case 'equals':
                    handleEquals();
                    break;
                case 'clear':
                    resetState();
                    break;
            }
        });
    });
}());
