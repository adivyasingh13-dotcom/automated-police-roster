// Roster Grid and Reassignment Modal Interactions

function openOverrideModal(assignmentId, officerName, shiftName, dateStr) {
    document.getElementById('overrideAssignmentId').value = assignmentId;
    document.getElementById('overrideOfficerName').innerText = officerName;
    document.getElementById('overrideShiftDetails').innerText = shiftName + ' on ' + dateStr;
    
    var modalEl = document.getElementById('overrideModal');
    if (modalEl) {
        var modal = new bootstrap.Modal(modalEl);
        modal.show();
    }
}
