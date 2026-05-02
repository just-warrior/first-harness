/* Jira Calculator Plugin — AJAX logic, input state, history (Skill 11: Event Delegation) */
AJS.$(document).ready(function () {
    (function () {
        var $display     = AJS.$('#calc-display');
        var $historyList = AJS.$('#calc-history');
        var history      = [];

        var currentInput      = '0';
        var operand1          = null;
        var operator          = null;
        var waitingForOperand2 = false;
        var justCalculated    = false;
        var $activeOperatorBtn = null;

        function clearOperatorActive() {
            if ($activeOperatorBtn) {
                $activeOperatorBtn.removeClass('calc-btn-operator--active');
                $activeOperatorBtn = null;
            }
        }

        function updateDisplay(val) {
            currentInput = String(val);
            $display.text(currentInput);
        }

        function renderHistory() {
            $historyList.empty();
            if (history.length === 0) {
                $historyList.append(AJS.$('<li>').addClass('calc-history-empty').text('계산 이력이 없습니다.'));
                return;
            }
            for (var i = 0; i < history.length; i++) {
                $historyList.append(AJS.$('<li>').text(history[i]));
            }
        }

        function addHistory(expression) {
            history.unshift(expression);
            if (history.length > 5) {
                history.pop();
            }
            renderHistory();
        }

        function clearAll() {
            currentInput       = '0';
            operand1           = null;
            operator           = null;
            waitingForOperand2 = false;
            justCalculated     = false;
            updateDisplay('0');
        }

        // Event delegation — no inline handlers (Skill 11, PITFALL-05)
        AJS.$('.calc-grid').on('click', '.calc-btn', function () {
            var action = AJS.$(this).data('action');
            var value  = AJS.$(this).data('value');

            if (action === 'digit') {
                if (waitingForOperand2 || justCalculated) {
                    currentInput       = String(value);
                    waitingForOperand2 = false;
                    justCalculated     = false;
                    clearOperatorActive();
                } else {
                    currentInput = (currentInput === '0') ? String(value) : currentInput + String(value);
                }
                updateDisplay(currentInput);

            } else if (action === 'decimal') {
                if (waitingForOperand2 || justCalculated) {
                    currentInput       = '0.';
                    waitingForOperand2 = false;
                    justCalculated     = false;
                    clearOperatorActive();
                } else if (currentInput.indexOf('.') === -1) {
                    currentInput += '.';
                }
                updateDisplay(currentInput);

            } else if (action === 'operator') {
                if (currentInput !== 'Error') {
                    operand1           = currentInput;
                    operator           = String(value);
                    waitingForOperand2 = true;
                    justCalculated     = false;
                    clearOperatorActive();
                    $activeOperatorBtn = AJS.$(this);
                    $activeOperatorBtn.addClass('calc-btn-operator--active');
                }

            } else if (action === 'equals') {
                if (operand1 === null || operator === null || currentInput === 'Error') {
                    return;
                }
                var operand2 = currentInput;
                AJS.$.ajax({
                    url:         AJS.contextPath() + '/rest/calculator/1.0/calculate',
                    type:        'POST',
                    contentType: 'application/json',
                    dataType:    'json',
                    data: JSON.stringify({
                        operand1: operand1,
                        operator: operator,
                        operand2: operand2
                    }),
                    success: function (response) {
                        updateDisplay(String(response.result));
                        addHistory(response.expression);
                        operand1       = null;
                        operator       = null;
                        justCalculated = true;
                        clearOperatorActive();
                    },
                    error: function () {
                        updateDisplay('Error');
                        operand1           = null;
                        operator           = null;
                        waitingForOperand2 = false;
                        justCalculated     = false;
                        clearOperatorActive();
                    }
                });

            } else if (action === 'clear') {
                clearOperatorActive();
                clearAll();

            } else if (action === 'sign') {
                if (currentInput !== '0' && currentInput !== 'Error') {
                    var toggled = String(parseFloat(currentInput) * -1);
                    updateDisplay(toggled);
                }

            } else if (action === 'percent') {
                if (currentInput !== 'Error') {
                    updateDisplay(String(parseFloat(currentInput) / 100));
                }
            }
        });
    })();
});
