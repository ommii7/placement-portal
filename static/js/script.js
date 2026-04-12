// Job search with autocomplete
$(document).ready(function() {
    $('#job-search').on('input', function() {
        let query = $(this).val();
        if (query.length > 2) {
            $.ajax({
                url: '/api/jobs/search',
                method: 'GET',
                data: {q: query},
                success: function(data) {
                    displaySearchResults(data);
                }
            });
        }
    });
    
    // Apply filters
    $('#apply-filters').click(function() {
        let jobType = $('#job-type').val();
        let minSalary = $('#min-salary').val();
        window.location.href = `/jobs?job_type=${jobType}&min_salary=${minSalary}`;
    });
    
    // Subscription plan selection
    $('.select-plan').click(function() {
        let plan = $(this).data('plan');
        $('#selected-plan').val(plan);
        $('#payment-form').submit();
    });
    
    // Real-time notifications (simulated)
    function checkNotifications() {
        $.ajax({
            url: '/api/notifications',
            method: 'GET',
            success: function(data) {
                if (data.count > 0) {
                    $('#notification-badge').show().text(data.count);
                }
            }
        });
    }
    
    // Check every 30 seconds
    setInterval(checkNotifications, 30000);
    
    // Resume preview
    $('#resume-upload').change(function(e) {
        let file = e.target.files[0];
        if (file) {
            $('#resume-name').text(file.name);
            $('#parse-progress').show();
            
            // Simulate parsing
            setTimeout(function() {
                $('#parse-progress').hide();
                $('#parse-success').show().fadeOut(3000);
            }, 2000);
        }
    });
});

function displaySearchResults(jobs) {
    let resultsDiv = $('#search-results');
    resultsDiv.empty();
    
    if (jobs.length === 0) {
        resultsDiv.html('<p class="text-muted">No jobs found</p>');
        return;
    }
    
    jobs.forEach(job => {
        resultsDiv.append(`
            <div class="search-result-item p-3 border-bottom">
                <h6>${job.title}</h6>
                <p class="mb-0">${job.company} • ${job.location}</p>
                <small class="text-success">₹${job.salary_min} - ${job.salary_max} LPA</small>
            </div>
        `);
    });
}

// Apply for job with subscription check
function applyForJob(jobId, isPremium) {
    if (isPremium) {
        Swal.fire({
            title: 'Premium Job',
            text: 'This job requires an active subscription. Would you like to subscribe?',
            icon: 'info',
            showCancelButton: true,
            confirmButtonText: 'Subscribe Now',
            cancelButtonText: 'Cancel'
        }).then((result) => {
            if (result.isConfirmed) {
                window.location.href = '/payment';
            }
        });
    } else {
        $('#apply-form-' + jobId).submit();
    }
}

// Document upload with preview
function previewDocument(input) {
    if (input.files && input.files[0]) {
        let reader = new FileReader();
        reader.onload = function(e) {
            $('#document-preview').attr('src', e.target.result);
        };
        reader.readAsDataURL(input.files[0]);
    }
}

// Dashboard charts (for admin)
function initRevenueChart(data) {
    const ctx = document.getElementById('revenue-chart').getContext('2d');
    new Chart(ctx, {
        type: 'line',
        data: {
            labels: data.months,
            datasets: [{
                label: 'Revenue (₹)',
                data: data.values,
                borderColor: '#2563eb',
                backgroundColor: 'rgba(37, 99, 235, 0.1)',
                tension: 0.4
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: {
                    position: 'top',
                }
            }
        }
    });
}