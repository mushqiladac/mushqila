// Flight Search Widget Functionality
(function() {
    'use strict';

    // Configuration
    const CONFIG = {
        airportSearchUrl: '/flights/api/airport-search/',
        flightSearchUrl: '/flights/api/flight-search/',
        minSearchLength: 2,
        searchDelay: 300
    };

    // State management
    const state = {
        origin: { code: 'DAC', city: 'Dhaka', country: 'Bangladesh', name: 'Hazrat Shahjalal International Airport' },
        destination: { code: 'CXB', city: "Cox's Bazar", country: 'Bangladesh', name: "Cox's Bazar Airport" },
        departureDate: null,
        returnDate: null,
        passengers: { adults: 1, children: 0, infants: 0 },
        cabinClass: 'economy',
        tripType: 'one-way',
        fareType: 'regular'
    };

    // Initialize on DOM ready
    document.addEventListener('DOMContentLoaded', function() {
        initializeSearchWidget();
    });

    function initializeSearchWidget() {
        initializeDatePickers();
        initializeAirportAutocomplete();
        initializePassengerSelector();
        initializeTripTypeButtons();
        initializeFareTypeButtons();
        initializeSwapButton();
        initializeSearchButton();
        updatePassengerDisplay();
    }

    // Date Picker Initialization
    function initializeDatePickers() {
        const today = new Date();
        today.setHours(0, 0, 0, 0);

        // Departure date picker
        const departurePicker = flatpickr('#departure-date', {
            minDate: today,
            dateFormat: 'Y-m-d',
            defaultDate: new Date(today.getTime() + 7 * 24 * 60 * 60 * 1000), // 7 days from now
            onChange: function(selectedDates, dateStr) {
                state.departureDate = dateStr;
                updateDateDisplay('departure', selectedDates[0]);
                
                // Update return date minimum
                if (returnPicker) {
                    returnPicker.set('minDate', selectedDates[0]);
                    if (state.returnDate && new Date(state.returnDate) < selectedDates[0]) {
                        returnPicker.clear();
                    }
                }
            }
        });

        // Return date picker
        const returnPicker = flatpickr('#return-date', {
            minDate: today,
            dateFormat: 'Y-m-d',
            onChange: function(selectedDates, dateStr) {
                state.returnDate = dateStr;
                updateDateDisplay('return', selectedDates[0]);
            }
        });

        // Set initial departure date
        const initialDate = new Date(today.getTime() + 7 * 24 * 60 * 60 * 1000);
        state.departureDate = initialDate.toISOString().split('T')[0];
        updateDateDisplay('departure', initialDate);
    }

    function updateDateDisplay(type, date) {
        const monthNames = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
        const dayNames = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];
        
        const day = date.getDate();
        const month = monthNames[date.getMonth()];
        const year = date.getFullYear();
        const dayName = dayNames[date.getDay()];

        const labelEl = document.querySelector(`#${type}-date-label`);
        const inputEl = document.querySelector(`#${type}-date-input`);
        const detailEl = document.querySelector(`#${type}-date-detail`);

        if (labelEl) labelEl.textContent = day;
        if (inputEl) inputEl.value = month;
        if (detailEl) detailEl.textContent = `${dayName}, ${year}`;
    }

    // Airport Autocomplete
    function initializeAirportAutocomplete() {
        const originInput = document.getElementById('origin-input');
        const destinationInput = document.getElementById('destination-input');

        if (originInput) {
            setupAirportSearch(originInput, 'origin');
        }
        if (destinationInput) {
            setupAirportSearch(destinationInput, 'destination');
        }
    }

    let searchTimeout;
    function setupAirportSearch(input, type) {
        const resultsContainer = document.getElementById(`${type}-results`);
        
        input.addEventListener('input', function() {
            clearTimeout(searchTimeout);
            const query = this.value.trim();

            if (query.length < CONFIG.minSearchLength) {
                hideResults(resultsContainer);
                return;
            }

            searchTimeout = setTimeout(() => {
                searchAirports(query, resultsContainer, type);
            }, CONFIG.searchDelay);
        });

        input.addEventListener('focus', function() {
            if (this.value.trim().length >= CONFIG.minSearchLength) {
                searchAirports(this.value.trim(), resultsContainer, type);
            }
        });

        // Close results when clicking outside
        document.addEventListener('click', function(e) {
            if (!input.contains(e.target) && !resultsContainer.contains(e.target)) {
                hideResults(resultsContainer);
            }
        });
    }

    function searchAirports(query, container, type) {
        fetch(`${CONFIG.airportSearchUrl}?q=${encodeURIComponent(query)}`)
            .then(response => response.json())
            .then(data => {
                displayAirportResults(data.results, container, type);
            })
            .catch(error => {
                console.error('Airport search error:', error);
            });
    }

    function displayAirportResults(results, container, type) {
        if (!results || results.length === 0) {
            container.innerHTML = '<div class="autocomplete-item">No airports found</div>';
            container.style.display = 'block';
            return;
        }

        container.innerHTML = results.map(airport => `
            <div class="autocomplete-item" data-code="${airport.code}" data-city="${airport.city}" 
                 data-country="${airport.country}" data-name="${airport.name}">
                <div class="airport-code">${airport.code}</div>
                <div class="airport-info">
                    <div class="airport-city">${airport.city}, ${airport.country}</div>
                    <div class="airport-name">${airport.name}</div>
                </div>
            </div>
        `).join('');

        container.style.display = 'block';

        // Add click handlers
        container.querySelectorAll('.autocomplete-item').forEach(item => {
            item.addEventListener('click', function() {
                selectAirport(this, type);
            });
        });
    }

    function selectAirport(item, type) {
        const airport = {
            code: item.dataset.code,
            city: item.dataset.city,
            country: item.dataset.country,
            name: item.dataset.name
        };

        state[type] = airport;

        // Update UI
        document.getElementById(`${type}-code`).textContent = airport.code;
        document.getElementById(`${type}-input`).value = airport.city;
        document.getElementById(`${type}-detail`).textContent = `${airport.country}, ${airport.name}`;

        // Hide results
        hideResults(document.getElementById(`${type}-results`));
    }

    function hideResults(container) {
        if (container) {
            container.style.display = 'none';
        }
    }

    // Passenger Selector
    function initializePassengerSelector() {
        const passengerInput = document.getElementById('passenger-input');
        const passengerModal = document.getElementById('passenger-modal');
        const closeModal = document.querySelector('.close-modal');
        const doneButton = document.getElementById('passenger-done');

        if (passengerInput) {
            passengerInput.addEventListener('click', function() {
                passengerModal.style.display = 'flex';
            });
        }

        if (closeModal) {
            closeModal.addEventListener('click', function() {
                passengerModal.style.display = 'none';
            });
        }

        if (doneButton) {
            doneButton.addEventListener('click', function() {
                passengerModal.style.display = 'none';
                updatePassengerDisplay();
            });
        }

        // Passenger counters
        setupCounter('adults', 1, 9);
        setupCounter('children', 0, 8);
        setupCounter('infants', 0, 4);

        // Cabin class selection
        document.querySelectorAll('.cabin-option').forEach(option => {
            option.addEventListener('click', function() {
                document.querySelectorAll('.cabin-option').forEach(opt => opt.classList.remove('active'));
                this.classList.add('active');
                state.cabinClass = this.dataset.class;
                updatePassengerDisplay();
            });
        });
    }

    function setupCounter(type, min, max) {
        const decreaseBtn = document.getElementById(`${type}-decrease`);
        const increaseBtn = document.getElementById(`${type}-increase`);
        const countEl = document.getElementById(`${type}-count`);

        if (decreaseBtn) {
            decreaseBtn.addEventListener('click', function() {
                if (state.passengers[type] > min) {
                    state.passengers[type]--;
                    countEl.textContent = state.passengers[type];
                    updatePassengerDisplay();
                }
            });
        }

        if (increaseBtn) {
            increaseBtn.addEventListener('click', function() {
                if (state.passengers[type] < max) {
                    state.passengers[type]++;
                    countEl.textContent = state.passengers[type];
                    updatePassengerDisplay();
                }
            });
        }
    }

    function updatePassengerDisplay() {
        const total = state.passengers.adults + state.passengers.children + state.passengers.infants;
        const travelerText = total === 1 ? '1 Traveller' : `${total} Travellers`;
        const classText = state.cabinClass.charAt(0).toUpperCase() + state.cabinClass.slice(1);

        document.getElementById('passenger-label').textContent = travelerText;
        document.getElementById('passenger-input').value = classText;
    }

    // Trip Type Buttons
    function initializeTripTypeButtons() {
        document.querySelectorAll('.trip-type-btn').forEach(btn => {
            btn.addEventListener('click', function() {
                document.querySelectorAll('.trip-type-btn').forEach(b => b.classList.remove('active'));
                this.classList.add('active');
                state.tripType = this.querySelector('input').value;
                
                // Show/hide return date based on trip type
                const returnDateField = document.querySelector('.return-date-field');
                if (returnDateField) {
                    returnDateField.style.display = state.tripType === 'round-trip' ? 'block' : 'none';
                }
            });
        });
    }

    // Fare Type Buttons
    function initializeFareTypeButtons() {
        document.querySelectorAll('input[name="fare-type"]').forEach(radio => {
            radio.addEventListener('change', function() {
                state.fareType = this.value;
            });
        });
    }

    // Swap Button
    function initializeSwapButton() {
        const swapBtn = document.querySelector('.swap-button');
        if (swapBtn) {
            swapBtn.addEventListener('click', function() {
                // Swap origin and destination
                const temp = state.origin;
                state.origin = state.destination;
                state.destination = temp;

                // Update UI
                document.getElementById('origin-code').textContent = state.origin.code;
                document.getElementById('origin-input').value = state.origin.city;
                document.getElementById('origin-detail').textContent = `${state.origin.country}, ${state.origin.name}`;

                document.getElementById('destination-code').textContent = state.destination.code;
                document.getElementById('destination-input').value = state.destination.city;
                document.getElementById('destination-detail').textContent = `${state.destination.country}, ${state.destination.name}`;

                // Animate button
                this.style.transform = 'rotate(180deg)';
                setTimeout(() => {
                    this.style.transform = 'rotate(0deg)';
                }, 300);
            });
        }
    }

    // Search Button
    function initializeSearchButton() {
        const searchBtn = document.getElementById('search-flights-btn');
        if (searchBtn) {
            searchBtn.addEventListener('click', function() {
                performFlightSearch();
            });
        }
    }

    function performFlightSearch() {
        // Validation
        if (!state.origin || !state.destination) {
            showAlert('Please select origin and destination airports', 'error');
            return;
        }

        if (!state.departureDate) {
            showAlert('Please select departure date', 'error');
            return;
        }

        if (state.tripType === 'round-trip' && !state.returnDate) {
            showAlert('Please select return date for round trip', 'error');
            return;
        }

        // Prepare search data
        const searchData = {
            search_type: state.tripType.replace('-', '_'), // Convert 'one-way' to 'one_way'
            origin: state.origin.code,
            destination: state.destination.code,
            departure_date: state.departureDate,
            return_date: state.returnDate,
            adults: state.passengers.adults,
            children: state.passengers.children,
            infants: state.passengers.infants,
            cabin_class: state.cabinClass
        };

        // Show loading
        const searchBtn = document.getElementById('search-flights-btn');
        const originalText = searchBtn.innerHTML;
        searchBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Searching...';
        searchBtn.disabled = true;

        // Send AJAX request
        fetch(CONFIG.flightSearchUrl, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: JSON.stringify(searchData)
        })
        .then(response => response.json())
        .then(data => {
            searchBtn.innerHTML = originalText;
            searchBtn.disabled = false;

            if (data.success) {
                displayFlightResults(data.flights);
                showAlert(data.message || 'Flights found!', 'success');
            } else {
                showAlert(data.error || 'Search failed', 'error');
            }
        })
        .catch(error => {
            searchBtn.innerHTML = originalText;
            searchBtn.disabled = false;
            showAlert('Network error. Please try again.', 'error');
            console.error('Search error:', error);
        });
    }

    function displayFlightResults(flights) {
        console.log('Flight results:', flights);
        // TODO: Display results in a modal or redirect to results page
        alert(`Found ${flights.length} flights!\n\nDemo data:\n${JSON.stringify(flights[0], null, 2)}`);
    }

    function showAlert(message, type) {
        // Simple alert for now - can be replaced with better UI
        const alertClass = type === 'error' ? 'danger' : type;
        const alertDiv = document.createElement('div');
        alertDiv.className = `alert alert-${alertClass} alert-dismissible fade show`;
        alertDiv.style.position = 'fixed';
        alertDiv.style.top = '20px';
        alertDiv.style.right = '20px';
        alertDiv.style.zIndex = '9999';
        alertDiv.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        document.body.appendChild(alertDiv);

        setTimeout(() => {
            alertDiv.remove();
        }, 5000);
    }

    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }

})();
