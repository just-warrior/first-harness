(function () {
    'use strict';

    /* ── State ── */
    var currentInput = '';
    var pendingNum = null;
    var pendingOp = null;
    var justCalculated = false;
    var history = [];

    /* ── DOM helpers ── */
    function setDisplay(val) {
        AJS.$('#calc-display').text(String(val));
    }

    function setExpression(val) {
        AJS.$('#calc-expression').text(val || ' ');
    }

    function updateHistoryPanel() {
        var $list = AJS.$('#calc-history-list');
        $list.empty();
        if (history.length === 0) {
            $list.append('<li class="calc-history-empty">No calculations yet.</li>');
            return;
        }
        for (var i = history.length - 1; i >= 0; i--) {
            $list.append('<li>' + AJS.escapeHtml(history[i]) + '</li>');
        }
    }

    /* ── Input helpers ── */
    function appendDigit(digit) {
        if (justCalculated) {
            currentInput = digit;
            justCalculated = false;
        } else {
            if (currentInput === '0' && digit !== '.') {
                currentInput = digit;
            } else {
                currentInput += digit;
            }
        }
        setDisplay(currentInput || '0');
    }

    function appendDecimal() {
        if (justCalculated) {
            currentInput = '0.';
            justCalculated = false;
        } else if (currentInput.indexOf('.') === -1) {
            currentInput = (currentInput || '0') + '.';
        }
        setDisplay(currentInput);
    }

    function toggleSign() {
        if (!currentInput || currentInput === '0') return;
        if (currentInput.charAt(0) === '-') {
            currentInput = currentInput.slice(1);
        } else {
            currentInput = '-' + currentInput;
        }
        setDisplay(currentInput);
    }

    function clearAll() {
        currentInput = '';
        pendingNum = null;
        pendingOp = null;
        justCalculated = false;
        setDisplay('0');
        setExpression('');
    }

    function selectOperator(op) {
        if (currentInput === '' && pendingNum !== null) {
            pendingOp = op;
            setExpression(String(pendingNum) + ' ' + op);
            return;
        }
        if (currentInput !== '') {
            if (pendingNum !== null && pendingOp !== null) {
                calculate(function (result) {
                    pendingNum = result;
                    pendingOp = op;
                    currentInput = '';
                    justCalculated = false;
                    setDisplay(String(result));
                    setExpression(String(result) + ' ' + op);
                });
                return;
            }
            pendingNum = parseFloat(currentInput);
            pendingOp = op;
            setExpression(currentInput + ' ' + op);
            currentInput = '';
        }
    }

    /* ── REST call ── */
    function calculate(callback) {
        if (pendingNum === null || pendingOp === null || currentInput === '') return;

        var payload = {
            num1: String(pendingNum),
            num2: currentInput,
            operator: pendingOp
        };

        var expression = String(pendingNum) + ' ' + pendingOp + ' ' + currentInput;

        AJS.$.ajax({
            url: AJS.contextPath() + '/rest/calculator/1.0/calculate',
            type: 'POST',
            contentType: 'application/json',
            dataType: 'json',
            data: JSON.stringify(payload),
            success: function (data) {
                if (data && data.error) {
                    setDisplay('Error');
                    setExpression(data.error);
                    pendingNum = null;
                    pendingOp = null;
                    currentInput = '';
                    justCalculated = true;
                    return;
                }
                var result = data.result;
                var displayResult = (result % 1 === 0) ? String(result) : String(parseFloat(result.toFixed(10)));

                setDisplay(displayResult);
                setExpression(expression + ' =');

                history.push(expression + ' = ' + displayResult);
                if (history.length > 5) history.shift();
                updateHistoryPanel();

                pendingNum = null;
                pendingOp = null;
                currentInput = displayResult;
                justCalculated = true;

                if (typeof callback === 'function') callback(result);
            },
            error: function (xhr) {
                var msg = 'Calculation error';
                try {
                    var body = JSON.parse(xhr.responseText);
                    if (body && body.error) msg = body.error;
                } catch (e) { /* ignore */ }
                setDisplay('Error');
                setExpression(msg);
                pendingNum = null;
                pendingOp = null;
                currentInput = '';
                justCalculated = true;
            }
        });
    }

    /* ── Event delegation (Skill 11) ── */
    AJS.$(document).ready(function () {
        AJS.$('.calc-grid').on('click', '.calc-btn', function () {
            var $btn = AJS.$(this);
            var action = $btn.data('action');
            var value  = $btn.data('value');

            switch (action) {
                case 'number':
                    appendDigit(String(value));
                    break;
                case 'decimal':
                    appendDecimal();
                    break;
                case 'sign':
                    toggleSign();
                    break;
                case 'clear':
                    clearAll();
                    break;
                case 'operator':
                    selectOperator(String(value));
                    break;
                case 'equals':
                    calculate();
                    break;
            }
        });

        updateHistoryPanel();
    });

}());
