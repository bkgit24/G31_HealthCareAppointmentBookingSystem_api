const specialtyInfo = {
    "Cardiology": {
        description: "Cardiology is a medical specialty focused on diagnosing and treating heart conditions. Cardiologists are experts in managing conditions like heart disease, hypertension, and cardiac arrhythmias. They perform various diagnostic tests and procedures to evaluate heart health.",
        stats: {
            "Average Salary": "$351,000/year",
            "Training Duration": "6-7 years",
            "Common Procedures": "80+ types",
            "Patient Volume": "3000+/year"
        }
    },
    "Neurology": {
        description: "Neurology deals with disorders of the nervous system, including the brain, spinal cord, and peripheral nerves. Neurologists treat conditions like epilepsy, stroke, multiple sclerosis, and Parkinson's disease. They use advanced imaging and diagnostic techniques to understand neural functions.",
        stats: {
            "Average Salary": "$280,000/year",
            "Training Duration": "4 years",
            "Common Conditions": "100+ types",
            "Patient Volume": "2500+/year"
        }
    },
    "Pediatrics": {
        description: "Pediatrics focuses on the medical care of infants, children, and adolescents. Pediatricians manage everything from routine check-ups to complex childhood diseases. They play a crucial role in monitoring growth, development, and vaccination schedules.",
        stats: {
            "Average Salary": "$232,000/year",
            "Training Duration": "3 years",
            "Age Range": "0-18 years",
            "Patient Volume": "4000+/year"
        }
    },
    "Surgery": {
        description: "Surgery is a medical specialty involving operative procedures to treat injuries, diseases, and deformities. Surgeons use both traditional and minimally invasive techniques. They require extensive training in specific surgical procedures and pre/post-operative care.",
        stats: {
            "Average Salary": "$401,000/year",
            "Training Duration": "5-7 years",
            "Procedures": "300+ types",
            "Operations/Year": "250-300"
        }
    },
    "Psychiatry": {
        description: "Psychiatry focuses on the diagnosis, treatment, and prevention of mental, emotional, and behavioral disorders. Psychiatrists use various therapeutic approaches and medications to help patients with conditions like depression, anxiety, and schizophrenia.",
        stats: {
            "Average Salary": "$249,000/year",
            "Training Duration": "4 years",
            "Treatment Methods": "20+ types",
            "Patient Volume": "1500+/year"
        }
    },
    "Ophthalmology": {
        description: "Ophthalmology specializes in eye and vision care. Ophthalmologists diagnose and treat various eye conditions, perform surgery, and prescribe corrective lenses. They handle everything from routine vision problems to complex eye diseases.",
        stats: {
            "Average Salary": "$309,000/year",
            "Training Duration": "4 years",
            "Procedures": "150+ types",
            "Patient Volume": "3500+/year"
        }
    }
};

function openModal(specialty) {
    const modal = document.getElementById('modalOverlay');
    const titleEl = document.getElementById('modalTitle');
    const contentEl = document.getElementById('modalContent');
    const statsEl = document.getElementById('modalStats');

    titleEl.textContent = specialty;
    contentEl.textContent = specialtyInfo[specialty].description;

    // Clear previous stats
    statsEl.innerHTML = '';

    // Add new stats
    Object.entries(specialtyInfo[specialty].stats).forEach(([label, value]) => {
        const statItem = document.createElement('div');
        statItem.className = 'stat-item';
        statItem.innerHTML = `
                    <div class="stat-value">${value}</div>
                    <div class="stat-label">${label}</div>
                `;
        statsEl.appendChild(statItem);
    });

    modal.style.display = 'block';
    document.body.style.overflow = 'hidden';
}

function closeModal() {
    const modal = document.getElementById('modalOverlay');
    modal.style.display = 'none';
    document.body.style.overflow = 'auto';
}

// Add click listeners to specialty cards
document.querySelectorAll('.specialty-card').forEach(card => {
    card.addEventListener('click', () => {
        const specialty = card.getAttribute('data-specialty');
        openModal(specialty);
    });
});

// Close modal when clicking outside
document.getElementById('modalOverlay').addEventListener('click', (e) => {
    if (e.target === document.getElementById('modalOverlay')) {
        closeModal();
    }
});



const hospitalInfo = {
    "Anderson Hospital": {
        location: "Mayur Vihar, Delhi",
        description: "Anderson Hospital is a leading multi-specialty healthcare facility in Delhi, known for its cutting-edge medical technology and expert healthcare professionals. Established in 1995, it has grown to become one of the most trusted medical institutions in North India.",
        stats: {
            "Total Beds": "650+",
            "ICU Units": "45",
            "Operating Theaters": "24",
            "Annual Patients": "200,000+",
            "Emergency Response Time": "< 10 mins",
            "Success Rate": "98.5%"
        },
        departments: [
            "Cardiology", "Neurology", "Orthopedics", "Oncology", 
            "Pediatrics", "General Surgery", "Emergency Medicine",
            "Dental Care", "Ophthalmology", "Psychiatry",
            "Dermatology", "Gynecology"
        ],
        facilities: [
            "24/7 Emergency Services",
            "Advanced Diagnostic Center",
            "Modern Laboratory",
            "Specialized Cancer Center",
            "Rehabilitation Center",
            "International Patient Services"
        ]
    },
    "Chen Hospital": {
        location: "Murgudas Road, Chennai",
        description: "Chen Hospital is renowned for its excellence in cardiac care and pediatric services. Founded in 2001, it has pioneered numerous innovative medical procedures in South India and maintains strong international collaborations for advanced treatments.",
        stats: {
            "Total Beds": "480+",
            "ICU Units": "38",
            "Operating Theaters": "18",
            "Annual Patients": "175,000+",
            "Emergency Response Time": "< 8 mins",
            "Success Rate": "97.8%"
        },
        departments: [
            "Cardiology", "Pediatrics", "Neurosurgery",
            "Internal Medicine", "Orthopedics", "Pulmonology",
            "Nephrology", "Urology", "ENT",
            "Gastroenterology", "Endocrinology"
        ],
        facilities: [
            "Specialized Children's Wing",
            "Heart Institute",
            "Digital Imaging Center",
            "Physical Therapy Unit",
            "24/7 Pharmacy",
            "Telemedicine Services"
        ]
    },
    "Johns Hopkins Hospital": {
        location: "Bandra, Mumbai",
        description: "Johns Hopkins Hospital Mumbai is a state-of-the-art medical facility that combines international healthcare standards with cutting-edge technology. It's particularly known for its oncology and neuroscience departments, serving patients from across South Asia.",
        stats: {
            "Total Beds": "750+",
            "ICU Units": "52",
            "Operating Theaters": "28",
            "Annual Patients": "250,000+",
            "Emergency Response Time": "< 5 mins",
            "Success Rate": "99.1%"
        },
        departments: [
            "Oncology", "Neuroscience", "Cardiac Sciences",
            "Transplant Center", "Robotics Surgery", "Emergency Medicine",
            "Nuclear Medicine", "Radiation Therapy", "Immunology",
            "Preventive Medicine", "Research Wing"
        ],
        facilities: [
            "Cancer Research Center",
            "Robot-Assisted Surgery Unit",
            "Advanced Imaging Center",
            "Clinical Research Department",
            "International Patient Lounge",
            "Air Ambulance Service"
        ]
    }
};

function openModal1(hospitalName) {
    const hospital = hospitalInfo[hospitalName];
    const modal = document.getElementById('modalOverlay1');
    const titleEl = document.getElementById('modalTitle1');
    const contentEl = document.getElementById('modalContent1');
    
    titleEl.textContent = hospitalName;
    
    contentEl.innerHTML = `
        <p><strong>Location:</strong> ${hospital.location}</p>
        <p>${hospital.description}</p>
        
        <div class="detail-section">
            <h4>Key Statistics</h4>
            <div class="hospital-details">
                ${Object.entries(hospital.stats).map(([key, value]) => `
                    <div>
                        <strong>${key}:</strong> ${value}
                    </div>
                `).join('')}
            </div>
        </div>
        
        <div class="detail-section">
            <h4>Key Departments</h4>
            <div class="department-list">
                ${hospital.departments.map(dept => `
                    <div class="department-item">${dept}</div>
                `).join('')}
            </div>
        </div>
        
        <div class="detail-section">
            <h4>Facilities & Services</h4>
            <ul>
                ${hospital.facilities.map(facility => `
                    <li>${facility}</li>
                `).join('')}
            </ul>
        </div>
    `;
    
    modal.style.display = 'block';
    document.body.style.overflow = 'hidden';
}

function closeModal1() {
    const modal = document.getElementById('modalOverlay1');
    modal.style.display = 'none';
    document.body.style.overflow = 'auto';
}

// Add click listeners to hospital cards
document.querySelectorAll('.view-button').forEach(button => {
    button.addEventListener('click', () => {
        const hospitalName = button.closest('.hospital-card').querySelector('h3').textContent;
        openModal1(hospitalName);
    });
});

// Close modal when clicking outside
document.getElementById('modalOverlay1').addEventListener('click', (e) => {
    if (e.target === document.getElementById('modalOverlay1')) {
        closeModal1();
    }
});