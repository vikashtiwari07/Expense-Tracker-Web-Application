document.addEventListener('DOMContentLoaded', function() {
    // Highlight selected row in the table
    const table = document.getElementById('expensesTable');
    if (table) {
        const rows = table.getElementsByTagName('tbody')[0].getElementsByTagName('tr');
        
        for (let row of rows) {
            row.addEventListener('click', function() {
                // Toggle selected class
                this.classList.toggle('selected');
            });
        }
    }
});

function getSelectedExpenseId() {
    const selectedRow = document.querySelector('#expensesTable tbody tr.selected');
    if (!selectedRow) {
        alert('Please select an expense first');
        return null;
    }
    return selectedRow.getAttribute('data-id');
}

function viewSelected() {
    const expenseId = getSelectedExpenseId();
    if (!expenseId) return;
    
    // In a real application, you would fetch the details from the server
    const row = document.querySelector(`#expensesTable tbody tr[data-id="${expenseId}"]`);
    const cells = row.getElementsByTagName('td');
    
    const details = `
        <p><strong>ID:</strong> ${cells[0].textContent}</p>
        <p><strong>Date:</strong> ${cells[1].textContent}</p>
        <p><strong>Payee:</strong> ${cells[2].textContent}</p>
        <p><strong>Description:</strong> ${cells[3].textContent}</p>
        <p><strong>Amount:</strong> ${cells[4].textContent}</p>
        <p><strong>Payment Mode:</strong> ${cells[5].textContent}</p>
    `;
    
    document.getElementById('expenseDetails').innerHTML = details;
    
    // Show the modal
    const modal = new bootstrap.Modal(document.getElementById('expenseModal'));
    modal.show();
}

function deleteSelected() {
    const expenseId = getSelectedExpenseId();
    if (!expenseId) return;
    
    if (confirm('Are you sure you want to delete the selected expense?')) {
        window.location.href = `/delete_expense/${expenseId}`;
    }
}

function editSelected() {
    const expenseId = getSelectedExpenseId();
    if (!expenseId) return;
    
    window.location.href = `/edit_expense/${expenseId}`;
}

function convertSelectedToWords() {
    const expenseId = getSelectedExpenseId();
    if (!expenseId) return;
    
    const row = document.querySelector(`#expensesTable tbody tr[data-id="${expenseId}"]`);
    const cells = row.getElementsByTagName('td');
    
    const message = `Your expense can be read like: \n"You paid ${cells[4].textContent} to ${cells[2].textContent} for ${cells[3].textContent} on ${cells[1].textContent} via ${cells[5].textContent}"`;
    alert(message);
}

function convertToWords() {
    const date = document.getElementById('date').value;
    const description = document.getElementById('description').value;
    const amount = document.getElementById('amount').value;
    const payee = document.getElementById('payee').value;
    const mode = document.getElementById('mode_of_payment').value;
    
    if (!date || !description || !amount || !payee || !mode) {
        alert('Please fill all fields first!');
        return;
    }
    
    const message = `Your expense can be read like: \n"You paid $${amount} to ${payee} for ${description} on ${date} via ${mode}"`;
    
    if (confirm(`${message}\n\nShould I add it to the database?`)) {
        document.querySelector('form').submit();
    }
}