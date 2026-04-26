(function($) {
    "use strict";

    $(function() {
        var currentOperand1 = '';
        var operator = '';
        var currentOperand2 = '';
        var isEnteringSecond = false;
        var history = [];

        var $display = $('#calc-display');
        var $historyList = $('#history-list');

        function updateDisplay(value) {
            $display.val(value || '0');
        }

        function getDisplayOp(op) {
            const opMap = { '*': '×', '/': '÷', '-': '−', '+': '+' };
            return opMap[op] || op;
        }

        function handleDigit(n) {
            if (isEnteringSecond) {
                currentOperand2 += n;
                updateDisplay(currentOperand1 + ' ' + getDisplayOp(operator) + ' ' + currentOperand2);
            } else {
                currentOperand1 += n;
                updateDisplay(currentOperand1);
            }
        }

        function handleOperator(op) {
            if (!currentOperand1) return;
            if (isEnteringSecond && currentOperand2) {
                // If user clicks another operator after entering full expression, calculate first
                calculate(function() {
                    operator = op;
                    isEnteringSecond = true;
                    updateDisplay(currentOperand1 + ' ' + getDisplayOp(operator));
                });
                return;
            }
            operator = op;
            isEnteringSecond = true;
            updateDisplay(currentOperand1 + ' ' + getDisplayOp(operator));
        }

        function handleBackspace() {
            if (isEnteringSecond) {
                if (currentOperand2) {
                    currentOperand2 = currentOperand2.slice(0, -1);
                    updateDisplay(currentOperand1 + ' ' + getDisplayOp(operator) + (currentOperand2 ? ' ' + currentOperand2 : ''));
                } else {
                    isEnteringSecond = false;
                    operator = '';
                    updateDisplay(currentOperand1);
                }
            } else {
                if (currentOperand1) {
                    currentOperand1 = currentOperand1.slice(0, -1);
                    updateDisplay(currentOperand1);
                }
            }
        }

        function handleDot() {
            if (isEnteringSecond) {
                if (currentOperand2.indexOf('.') === -1) {
                    currentOperand2 += (currentOperand2 ? '' : '0') + '.';
                    updateDisplay(currentOperand1 + ' ' + getDisplayOp(operator) + ' ' + currentOperand2);
                }
            } else {
                if (currentOperand1.indexOf('.') === -1) {
                    currentOperand1 += (currentOperand1 ? '' : '0') + '.';
                    updateDisplay(currentOperand1);
                }
            }
        }

        function calculate(callback) {
            if (!currentOperand1 || !operator || !currentOperand2) return;

            $display.addClass('loading');

            $.ajax({
                url: AJS.contextPath() + '/rest/calculator/1.0/calculate',
                type: 'POST',
                contentType: 'application/json',
                data: JSON.stringify({
                    operand1: currentOperand1,
                    operator: operator,
                    operand2: currentOperand2
                }),
                success: function(response) {
                    if (response.error) {
                        AJS.messages.error({ title: "Error", body: response.error });
                        clear();
                    } else {
                        var expr = currentOperand1 + ' ' + getDisplayOp(operator) + ' ' + currentOperand2 + ' = ' + response.result;
                        addHistory(expr);
                        
                        currentOperand1 = String(response.result);
                        operator = '';
                        currentOperand2 = '';
                        isEnteringSecond = false;
                        updateDisplay(currentOperand1);
                        if (callback) callback();
                    }
                },
                error: function(xhr) {
                    var errorMsg = "Calculation failed";
                    try {
                        var res = JSON.parse(xhr.responseText);
                        if (res.error) errorMsg = res.error;
                    } catch(e) {}
                    AJS.messages.error({ title: "Error", body: errorMsg });
                },
                complete: function() {
                    $display.removeClass('loading');
                }
            });
        }

        function clear() {
            currentOperand1 = '';
            operator = '';
            currentOperand2 = '';
            isEnteringSecond = false;
            updateDisplay('0');
        }

        function addHistory(expr) {
            history.unshift(expr);
            if (history.length > 5) history.pop();
            renderHistory();
        }

        function renderHistory() {
            $historyList.empty();
            if (history.length === 0) {
                $historyList.append('<li class="history-empty">No history yet</li>');
            } else {
                history.forEach(function(entry) {
                    $('<li>').text(entry).appendTo($historyList);
                });
            }
        }

        // --- Event Delegation ---
        $('.calc-grid').on('click', '.calc-btn', function(e) {
            e.preventDefault();
            var $btn = $(this);
            
            if ($btn.hasClass('btn-num')) {
                handleDigit($btn.text().trim());
            } else if ($btn.hasClass('btn-op')) {
                if ($btn.hasClass('btn-backspace')) {
                    handleBackspace();
                } else if ($btn.text().trim() === '.') {
                    handleDot();
                } else {
                    // Get operator from data-op or just the text
                    var op = $btn.data('op') || $btn.text().trim();
                    // Map display symbols back to internal operators
                    if (op === '÷') op = '/';
                    if (op === '×') op = '*';
                    if (op === '−') op = '-';
                    handleOperator(op);
                }
            } else if ($btn.hasClass('btn-clear')) {
                clear();
            } else if ($btn.hasClass('btn-equals')) {
                calculate();
            }
        });

        // Keyboard support (Bonus for better UX)
        $(document).on('keydown', function(e) {
            if (!$display.is(':visible')) return;
            
            var key = e.key;
            if (/[0-9]/.test(key)) handleDigit(key);
            else if (['+', '-', '*', '/'].indexOf(key) !== -1) handleOperator(key);
            else if (key === 'Enter' || key === '=') calculate();
            else if (key === 'Escape' || key.toLowerCase() === 'c') clear();
            else if (key === 'Backspace') handleBackspace();
            else if (key === '.') handleDot();
        });
    });
})(AJS.$);
