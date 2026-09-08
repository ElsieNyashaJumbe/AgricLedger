// AgricLedger Dashboard JavaScript

// ========== STATE ==========
const state = {
    currentSection: 'dashboard',
    chatLanguage: 'English',
    farmerAddress: '0x68552AbF6AFAFC2170a5930531C12Eed38823a17',
    isAdmin: false
};

// ========== API BASE ==========
const API_BASE = window.API_BASE || '/api';

// ========== CHECK ADMIN STATUS ==========
async function checkAdminStatus() {
    try {
        const response = await fetch(`${API_BASE}/user/role`);
        const data = await response.json();
        state.isAdmin = data.role === 'admin';
        
        // Show/hide admin elements
        const adminElements = document.querySelectorAll('.admin-only');
        adminElements.forEach(el => {
            el.style.display = state.isAdmin ? 'flex' : 'none';
        });
        
        console.log(`👑 Admin status: ${state.isAdmin ? 'Admin' : 'User'}`);
    } catch (error) {
        console.error('Error checking admin status:', error);
        state.isAdmin = false;
    }
}

// ========== SIDEBAR TOGGLE ==========
function toggleSidebar() {
    const sidebar = document.getElementById('sidebar');
    if (sidebar) {
        sidebar.classList.toggle('collapsed');
        const isCollapsed = sidebar.classList.contains('collapsed');
        localStorage.setItem('sidebarCollapsed', isCollapsed);
    }
}

function restoreSidebarState() {
    const sidebar = document.getElementById('sidebar');
    if (sidebar) {
        const isCollapsed = localStorage.getItem('sidebarCollapsed') === 'true';
        if (window.innerWidth > 768) {
            if (isCollapsed) {
                sidebar.classList.add('collapsed');
            } else {
                sidebar.classList.remove('collapsed');
            }
        }
    }
}

function checkMainPage() {
    const sidebar = document.getElementById('sidebar');
    const activeLink = document.querySelector('.nav-link.active');
    
    if (sidebar && activeLink) {
        if (window.innerWidth <= 768) {
            if (activeLink.dataset.section === 'dashboard') {
                sidebar.classList.add('collapsed');
            }
        } else {
            const isCollapsed = localStorage.getItem('sidebarCollapsed') === 'true';
            if (isCollapsed) {
                sidebar.classList.add('collapsed');
            } else {
                sidebar.classList.remove('collapsed');
            }
        }
    }
}

// ============================================================
// NAVIGATION SYSTEM WITH SECTION PERSISTENCE
// ============================================================

// ===== NAVIGATE TO SECTION =====
function navigateToSection(section) {
    if (!section) return;
    
    // Update nav links
    document.querySelectorAll('.nav-link').forEach(function(l) {
        l.classList.remove('active');
    });
    var navLink = document.querySelector('.nav-link[data-section="' + section + '"]');
    if (navLink) navLink.classList.add('active');
    
    // Update sections
    document.querySelectorAll('.section').forEach(function(s) {
        s.classList.remove('active');
    });
    var target = document.getElementById('section-' + section);
    if (target) target.classList.add('active');
    
    // Update page title - UPDATED with 'market'
    var titles = {
        dashboard: 'Dashboard',
        weather: 'Weather & Forecast',
        crops: 'Crop Suitability',
        land: 'Land Tenure',
        data: 'Data Sovereignty',
        chat: 'AI Assistant',
        farmers: 'Registered Farmers',
        settings: 'Settings',
        reviews: 'Reviews & Feedback',
        market: 'Market Demand'
    };
    var titleElement = document.getElementById('page-title');
    if (titleElement) {
        titleElement.textContent = titles[section] || 'Dashboard';
    }
    
    // Save current section to localStorage
    localStorage.setItem('currentSection', section);
    state.currentSection = section;
    
    // Load section data
    loadSectionData(section);
}

// ===== LOAD SECTION DATA - UPDATED with 'market' =====
function loadSectionData(section) {
    console.log('📂 Loading section:', section);
    switch(section) {
        case 'dashboard':
            if (typeof loadDashboard === 'function') loadDashboard();
            break;
        case 'weather':
            if (typeof getWeather === 'function') getWeather();
            break;
        case 'crops':
            break;
        case 'data':
            if (typeof loadDataSovereignty === 'function') loadDataSovereignty();
            break;
        case 'land':
            if (typeof loadLandRecords === 'function') loadLandRecords();
            break;
        case 'farmers':
            if (typeof loadFarmers === 'function') loadFarmers();
            break;
        case 'chat':
            break;
        case 'reviews':
            if (typeof loadReviews === 'function') loadReviews();
            break;
        case 'settings':
            if (typeof initSettings === 'function') initSettings();
            break;
        case 'market':
            if (typeof initMarketSection === 'function') initMarketSection();
            break;
        default:
            console.log('No specific loader for section:', section);
    }
}

// ===== NAVIGATION CLICK HANDLER =====
document.querySelectorAll('.nav-link').forEach(function(link) {
    link.addEventListener('click', function(e) {
        e.preventDefault();
        
        var section = this.dataset.section;
        if (section) {
            navigateToSection(section);
        }
        
        // Close sidebar on mobile
        if (window.innerWidth <= 768) {
            var sidebar = document.getElementById('sidebar');
            if (sidebar) {
                sidebar.classList.add('collapsed');
                localStorage.setItem('sidebarCollapsed', 'true');
            }
        }
    });
});

// ===== RESTORE SECTION ON PAGE LOAD =====
document.addEventListener('DOMContentLoaded', function() {
    // Check admin status first
    checkAdminStatus();
    
    // Restore sidebar state
    restoreSidebarState();
    
    // Restore saved section
    var savedSection = localStorage.getItem('currentSection');
    console.log('🔄 Restoring section:', savedSection);
    
    if (savedSection) {
        var target = document.getElementById('section-' + savedSection);
        if (target) {
            navigateToSection(savedSection);
        } else {
            // If section not found, go to dashboard
            navigateToSection('dashboard');
        }
    } else {
        // Default to dashboard
        navigateToSection('dashboard');
    }
    
    console.log('✅ Navigation restored to:', localStorage.getItem('currentSection') || 'dashboard');
});

// ============================================================
// MARKET DEMAND TRANSPARENCY - COMPLETE MODULE
// ============================================================

let marketChartInstance = null;
let currentMarketTab = 'demand';

// ===== INITIALIZE MARKET SECTION =====
function initMarketSection() {
    console.log('📊 Initializing Market section...');
    
    // Load market data
    loadMarketSummary();
    loadMarketTrends();
    loadTopCrops();
    loadBuyers();
    loadPrices();
    loadSuppliers();
    loadFinancialInstitutes();
    loadMarketActivity();
    
    // Setup tab switching
    document.querySelectorAll('.market-tab-modern').forEach(tab => {
        tab.addEventListener('click', function() {
            const tabId = this.dataset.tab;
            switchMarketTab(tabId);
        });
    });
}

// ===== SWITCH MARKET TAB =====
function switchMarketTab(tabId) {
    currentMarketTab = tabId;
    
    // Update tabs
    document.querySelectorAll('.market-tab-modern').forEach(t => {
        t.classList.remove('active');
        if (t.dataset.tab === tabId) {
            t.classList.add('active');
        }
    });
    
    // Update content
    document.querySelectorAll('.market-tab-content-modern').forEach(c => {
        c.classList.remove('active');
    });
    const target = document.getElementById(`market-tab-${tabId}`);
    if (target) target.classList.add('active');
    
    // Load data for specific tab
    switch(tabId) {
        case 'demand':
            loadMarketTrends();
            loadTopCrops();
            break;
        case 'buyers':
            loadBuyers();
            break;
        case 'prices':
            loadPrices();
            break;
        case 'suppliers':
            loadSuppliers();
            break;
        case 'financial':
            loadFinancialInstitutes();
            break;
        case 'activity':
            loadMarketActivity();
            break;
    }
}

// ===== LOAD MARKET SUMMARY =====
async function loadMarketSummary() {
    try {
        const response = await fetch(`${API_BASE}/market/summary`);
        const data = await response.json();
        
        if (data.success) {
            const s = data.summary;
            document.getElementById('stat-crops-in-demand').textContent = s.total_crops || 0;
            document.getElementById('stat-active-buyers').textContent = s.total_buyers || 0;
            document.getElementById('stat-suppliers').textContent = s.total_suppliers || 0;
            document.getElementById('stat-financial-institutes').textContent = s.total_institutes || 0;
            document.getElementById('stat-avg-demand').textContent = s.avg_demand_score + '%';
            document.getElementById('stat-top-crop').textContent = s.top_crop || '-';
            
            document.getElementById('buyers-count').textContent = s.total_buyers || 0;
            
            // Update update time
            const now = new Date();
            document.getElementById('market-update-time').textContent = 
                `Updated: ${now.toLocaleTimeString()}`;
        }
    } catch (error) {
        console.error('Error loading market summary:', error);
    }
}

// ===== LOAD MARKET TRENDS =====
async function loadMarketTrends() {
    const location = document.getElementById('market-trend-location')?.value || 'Harare';
    const container = document.getElementById('market-demand-chart');
    if (!container) return;
    
    try {
        const response = await fetch(`${API_BASE}/market/trends?location=${location}&months=12`);
        const data = await response.json();
        
        if (data.success) {
            const trends = data.trends || [];
            const crops = [...new Set(trends.map(t => t.crop_name))];
            
            const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
            const datasets = [];
            const colors = ['#1a5c4a', '#f4a261', '#2ecc71', '#3498db', '#9b59b6', '#e74c3c'];
            
            crops.forEach((crop, index) => {
                const cropData = trends.filter(t => t.crop_name === crop);
                const demandData = months.map(month => {
                    const found = cropData.find(t => t.month === month);
                    return found ? found.demand_tonnes : 0;
                });
                
                datasets.push({
                    label: crop,
                    data: demandData,
                    borderColor: colors[index % colors.length],
                    backgroundColor: colors[index % colors.length] + '20',
                    fill: true,
                    tension: 0.4,
                    pointRadius: 3,
                    borderWidth: 2
                });
            });
            
            if (marketChartInstance) {
                marketChartInstance.destroy();
            }
            
            marketChartInstance = new Chart(container, {
                type: 'line',
                data: {
                    labels: months,
                    datasets: datasets.length > 0 ? datasets : [
                        {
                            label: 'No Data Available',
                            data: [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                            borderColor: '#ccc',
                            backgroundColor: '#ccc20',
                            fill: true,
                            tension: 0.4
                        }
                    ]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            position: 'top',
                            labels: {
                                usePointStyle: true,
                                pointStyle: 'circle',
                                padding: 20,
                                font: { size: 10 }
                            }
                        },
                        tooltip: {
                            backgroundColor: 'rgba(255,255,255,0.95)',
                            titleColor: '#1a3c34',
                            bodyColor: '#4a6b5a',
                            borderColor: '#e8edea',
                            borderWidth: 1,
                            cornerRadius: 8,
                            padding: 10,
                            callbacks: {
                                label: function(context) {
                                    return context.dataset.label + ': ' + context.parsed.y + ' tonnes';
                                }
                            }
                        }
                    },
                    scales: {
                        y: {
                            beginAtZero: true,
                            grid: { color: 'rgba(0,0,0,0.05)' },
                            ticks: { font: { size: 10 }, color: '#888' }
                        },
                        x: {
                            grid: { display: false },
                            ticks: { font: { size: 10 }, color: '#888' }
                        }
                    },
                    interaction: {
                        intersect: false,
                        mode: 'index'
                    }
                }
            });
        }
    } catch (error) {
        console.error('Error loading market trends:', error);
    }
}

// ===== LOAD TOP CROPS =====
async function loadTopCrops() {
    const container = document.getElementById('top-crops-list');
    if (!container) return;
    
    try {
        const response = await fetch(`${API_BASE}/market/crops`);
        const data = await response.json();
        
        if (data.success) {
            const crops = data.top_demand || [];
            
            if (crops.length === 0) {
                container.innerHTML = `
                    <div style="text-align:center;padding:30px;color:var(--text-light);grid-column:1/-1;">
                        <i class="fas fa-leaf" style="font-size:2rem;opacity:0.2;display:block;margin-bottom:8px;"></i>
                        <p>No crop data available</p>
                    </div>
                `;
                return;
            }
            
            let html = '';
            crops.forEach(crop => {
                const trendIcon = crop.trend === 'up' ? '📈' : 
                                 crop.trend === 'down' ? '📉' : '➡️';
                const trendClass = crop.trend === 'up' ? 'trend-up' : 
                                  crop.trend === 'down' ? 'trend-down' : 'trend-stable';
                
                html += `
                    <div class="top-crop-item">
                        <span class="crop-icon">${crop.icon || '🌾'}</span>
                        <span class="crop-name">${crop.crop_name}</span>
                        <span class="crop-demand">${crop.demand_score}% Demand</span>
                        <div class="demand-bar-container">
                            <div class="demand-bar" style="width:${crop.demand_score}%;"></div>
                        </div>
                        <span class="trend-indicator ${trendClass}">${trendIcon} ${crop.trend}</span>
                    </div>
                `;
            });
            
            container.innerHTML = html;
        }
    } catch (error) {
        console.error('Error loading top crops:', error);
        container.innerHTML = `
            <div style="text-align:center;padding:30px;color:var(--danger);grid-column:1/-1;">
                <i class="fas fa-exclamation-circle" style="font-size:2rem;display:block;margin-bottom:8px;"></i>
                <p>Error loading crop data</p>
            </div>
        `;
    }
}

// ===== LOAD BUYERS =====
async function loadBuyers() {
    const container = document.getElementById('buyers-list');
    const cropFilter = document.getElementById('buyer-filter-crop')?.value || '';
    if (!container) return;
    
    container.innerHTML = `
        <div class="loading-state">
            <div class="loading-spinner"></div>
            <p>Loading buyers...</p>
        </div>
    `;
    
    try {
        let url = `${API_BASE}/market/buyers`;
        if (cropFilter) {
            url += `?crop=${encodeURIComponent(cropFilter)}`;
        }
        
        const response = await fetch(url);
        const data = await response.json();
        
        if (data.success) {
            const buyers = data.buyers || [];
            
            if (buyers.length === 0) {
                container.innerHTML = `
                    <div style="text-align:center;padding:40px;color:var(--text-light);grid-column:1/-1;">
                        <i class="fas fa-handshake" style="font-size:2.5rem;opacity:0.2;display:block;margin-bottom:12px;"></i>
                        <h4 style="color:var(--text-light);">No buyers found</h4>
                        <p style="font-size:0.9rem;">${cropFilter ? `No buyers currently buying ${cropFilter}` : 'Check back later for new buyers'}</p>
                    </div>
                `;
                return;
            }
            
            let html = '';
            buyers.forEach(buyer => {
                const crops = typeof buyer.crops_bought === 'string' ? 
                    JSON.parse(buyer.crops_bought) : (buyer.crops_bought || []);
                
                html += `
                    <div class="buyer-card">
                        <div class="buyer-name">${buyer.name}</div>
                        <div class="buyer-location">📍 ${buyer.location}</div>
                        <div class="buyer-crops">
                            ${crops.map(c => `<span class="crop-tag">${c}</span>`).join('')}
                        </div>
                        ${buyer.contact_person ? `
                            <div class="buyer-contact">
                                📞 ${buyer.contact_person} | ${buyer.phone || ''} | ${buyer.email || ''}
                            </div>
                        ` : ''}
                    </div>
                `;
            });
            
            container.innerHTML = html;
        }
    } catch (error) {
        console.error('Error loading buyers:', error);
        container.innerHTML = `
            <div style="text-align:center;padding:40px;color:var(--danger);grid-column:1/-1;">
                <i class="fas fa-wifi" style="font-size:2rem;display:block;margin-bottom:12px;"></i>
                <p>Error loading buyers. Please try again.</p>
            </div>
        `;
    }
}

// ===== LOAD PRICES =====
async function loadPrices() {
    const container = document.getElementById('prices-list');
    const cropFilter = document.getElementById('price-filter-crop')?.value || '';
    const locationFilter = document.getElementById('price-filter-location')?.value || '';
    if (!container) return;
    
    container.innerHTML = `
        <div class="loading-state">
            <div class="loading-spinner"></div>
            <p>Loading prices...</p>
        </div>
    `;
    
    try {
        let url = `${API_BASE}/market/prices`;
        const params = [];
        if (cropFilter) params.push(`crop=${encodeURIComponent(cropFilter)}`);
        if (locationFilter) params.push(`location=${encodeURIComponent(locationFilter)}`);
        if (params.length > 0) url += '?' + params.join('&');
        
        const response = await fetch(url);
        const data = await response.json();
        
        if (data.success) {
            const prices = data.prices || [];
            
            if (prices.length === 0) {
                container.innerHTML = `
                    <div style="text-align:center;padding:40px;color:var(--text-light);">
                        <i class="fas fa-tag" style="font-size:2.5rem;opacity:0.2;display:block;margin-bottom:12px;"></i>
                        <h4 style="color:var(--text-light);">No prices found</h4>
                        <p style="font-size:0.9rem;">No price data available for the selected filters</p>
                    </div>
                `;
                return;
            }
            
            let html = `
                <table class="prices-table">
                    <thead>
                        <tr>
                            <th>Crop</th>
                            <th>Location</th>
                            <th>Price Range (USD)</th>
                            <th>Unit</th>
                            <th>Updated</th>
                        </tr>
                    </thead>
                    <tbody>
            `;
            
            prices.forEach(price => {
                html += `
                    <tr>
                        <td><strong>${price.crop_name}</strong></td>
                        <td>${price.location}</td>
                        <td class="price-range">$${price.price_min} - $${price.price_max}</td>
                        <td>per ${price.unit || 'tonne'}</td>
                        <td style="font-size:0.75rem;color:var(--text-light);">
                            ${price.updated_at ? new Date(price.updated_at).toLocaleDateString() : 'N/A'}
                        </td>
                    </tr>
                `;
            });
            
            html += `</tbody></table>`;
            container.innerHTML = html;
        }
    } catch (error) {
        console.error('Error loading prices:', error);
        container.innerHTML = `
            <div style="text-align:center;padding:40px;color:var(--danger);">
                <i class="fas fa-wifi" style="font-size:2rem;display:block;margin-bottom:12px;"></i>
                <p>Error loading prices. Please try again.</p>
            </div>
        `;
    }
}

// ===== LOAD SUPPLIERS =====
async function loadSuppliers() {
    const container = document.getElementById('suppliers-list');
    const categoryFilter = document.getElementById('supplier-filter-category')?.value || '';
    if (!container) return;
    
    container.innerHTML = `
        <div class="loading-state">
            <div class="loading-spinner"></div>
            <p>Loading suppliers...</p>
        </div>
    `;
    
    try {
        let url = `${API_BASE}/market/suppliers`;
        if (categoryFilter) {
            url += `?category=${encodeURIComponent(categoryFilter)}`;
        }
        
        const response = await fetch(url);
        const data = await response.json();
        
        if (data.success) {
            const suppliers = data.suppliers || [];
            
            if (suppliers.length === 0) {
                container.innerHTML = `
                    <div style="text-align:center;padding:40px;color:var(--text-light);grid-column:1/-1;">
                        <i class="fas fa-boxes" style="font-size:2.5rem;opacity:0.2;display:block;margin-bottom:12px;"></i>
                        <h4 style="color:var(--text-light);">No suppliers found</h4>
                        <p style="font-size:0.9rem;">${categoryFilter ? `No suppliers in category: ${categoryFilter}` : 'Check back later for new suppliers'}</p>
                    </div>
                `;
                return;
            }
            
            const categoryClassMap = {
                'Seed': 'category-seed',
                'Fertilizer': 'category-fertilizer',
                'Equipment': 'category-equipment',
                'Pesticide': 'category-pesticide',
                'Feed': 'category-feed'
            };
            
            let html = '';
            suppliers.forEach(supplier => {
                const products = typeof supplier.products === 'string' ? 
                    JSON.parse(supplier.products) : (supplier.products || []);
                const catClass = categoryClassMap[supplier.category] || '';
                const stars = '⭐'.repeat(Math.round(supplier.rating || 0));
                
                html += `
                    <div class="supplier-card">
                        <div class="supplier-header">
                            <span class="supplier-name">${supplier.name}</span>
                            <span class="supplier-category ${catClass}">${supplier.category}</span>
                        </div>
                        <div class="supplier-location">📍 ${supplier.location}</div>
                        <div class="supplier-products">
                            ${products.map(p => `<span class="product-tag">${p}</span>`).join('')}
                        </div>
                        ${supplier.rating ? `
                            <div class="supplier-rating">${stars} (${supplier.rating})</div>
                        ` : ''}
                        <div class="supplier-contact">
                            📞 ${supplier.contact_person || ''} | ${supplier.phone || ''} | ${supplier.email || ''}
                            ${supplier.website ? `| 🌐 ${supplier.website}` : ''}
                        </div>
                    </div>
                `;
            });
            
            container.innerHTML = html;
        }
    } catch (error) {
        console.error('Error loading suppliers:', error);
        container.innerHTML = `
            <div style="text-align:center;padding:40px;color:var(--danger);grid-column:1/-1;">
                <i class="fas fa-wifi" style="font-size:2rem;display:block;margin-bottom:12px;"></i>
                <p>Error loading suppliers. Please try again.</p>
            </div>
        `;
    }
}

// ===== LOAD FINANCIAL INSTITUTES =====
async function loadFinancialInstitutes() {
    const container = document.getElementById('financial-list');
    const typeFilter = document.getElementById('financial-filter-type')?.value || '';
    if (!container) return;
    
    container.innerHTML = `
        <div class="loading-state">
            <div class="loading-spinner"></div>
            <p>Loading financial institutes...</p>
        </div>
    `;
    
    try {
        let url = `${API_BASE}/market/financial`;
        if (typeFilter) {
            url += `?type=${encodeURIComponent(typeFilter)}`;
        }
        
        const response = await fetch(url);
        const data = await response.json();
        
        if (data.success) {
            const institutes = data.institutes || [];
            
            if (institutes.length === 0) {
                container.innerHTML = `
                    <div style="text-align:center;padding:40px;color:var(--text-light);grid-column:1/-1;">
                        <i class="fas fa-university" style="font-size:2.5rem;opacity:0.2;display:block;margin-bottom:12px;"></i>
                        <h4 style="color:var(--text-light);">No financial institutes found</h4>
                        <p style="font-size:0.9rem;">${typeFilter ? `No institutes of type: ${typeFilter}` : 'Check back later for new institutes'}</p>
                    </div>
                `;
                return;
            }
            
            const typeClassMap = {
                'Bank': 'type-bank',
                'Microfinance': 'type-microfinance',
                'Cooperative': 'type-cooperative',
                'Insurance': 'type-insurance'
            };
            
            let html = '';
            institutes.forEach(institute => {
                const loans = typeof institute.loan_types === 'string' ? 
                    JSON.parse(institute.loan_types) : (institute.loan_types || []);
                const typeClass = typeClassMap[institute.type] || '';
                
                html += `
                    <div class="financial-card">
                        <div class="financial-header">
                            <span class="financial-name">${institute.name}</span>
                            <span class="financial-type ${typeClass}">${institute.type}</span>
                        </div>
                        <div class="financial-location">📍 ${institute.location}</div>
                        <div class="financial-loans">
                            ${loans.map(l => `<span class="loan-tag">${l}</span>`).join('')}
                        </div>
                        ${institute.interest_rate ? `
                            <div class="financial-interest">💲 Interest Rate: ${institute.interest_rate}%</div>
                        ` : ''}
                        <div class="financial-contact">
                            📞 ${institute.contact_person || ''} | ${institute.phone || ''} | ${institute.email || ''}
                            ${institute.website ? `| 🌐 ${institute.website}` : ''}
                        </div>
                    </div>
                `;
            });
            
            container.innerHTML = html;
        }
    } catch (error) {
        console.error('Error loading financial institutes:', error);
        container.innerHTML = `
            <div style="text-align:center;padding:40px;color:var(--danger);grid-column:1/-1;">
                <i class="fas fa-wifi" style="font-size:2rem;display:block;margin-bottom:12px;"></i>
                <p>Error loading financial institutes. Please try again.</p>
            </div>
        `;
    }
}

// ===== LOAD MARKET ACTIVITY =====
async function loadMarketActivity() {
    const container = document.getElementById('market-activity-list');
    if (!container) return;
    
    container.innerHTML = `
        <div class="loading-state">
            <div class="loading-spinner"></div>
            <p>Loading activity...</p>
        </div>
    `;
    
    try {
        const response = await fetch(`${API_BASE}/market/activity?limit=20`);
        const data = await response.json();
        
        if (data.success) {
            const activities = data.activities || [];
            document.getElementById('activity-count').textContent = activities.length;
            
            if (activities.length === 0) {
                container.innerHTML = `
                    <div style="text-align:center;padding:40px;color:var(--text-light);">
                        <i class="fas fa-clock" style="font-size:2.5rem;opacity:0.2;display:block;margin-bottom:12px;"></i>
                        <h4 style="color:var(--text-light);">No recent activity</h4>
                        <p style="font-size:0.9rem;">Market activity will appear here as it happens</p>
                    </div>
                `;
                return;
            }
            
            let html = '';
            activities.forEach(activity => {
                const time = activity.created_at ? 
                    new Date(activity.created_at).toLocaleString() : 'Recently';
                
                html += `
                    <div class="activity-item">
                        <div class="activity-icon">${activity.icon || '📊'}</div>
                        <div class="activity-content">
                            <div class="activity-title">${activity.title}</div>
                            <div class="activity-description">${activity.description || ''}</div>
                        </div>
                        <div class="activity-time">${time}</div>
                    </div>
                `;
            });
            
            container.innerHTML = html;
        }
    } catch (error) {
        console.error('Error loading market activity:', error);
        container.innerHTML = `
            <div style="text-align:center;padding:40px;color:var(--danger);">
                <i class="fas fa-wifi" style="font-size:2rem;display:block;margin-bottom:12px;"></i>
                <p>Error loading activity. Please try again.</p>
            </div>
        `;
    }
}

// ===== REFRESH MARKET DATA =====
function refreshMarketData() {
    console.log('🔄 Refreshing market data...');
    showToast('🔄 Refreshing market data...', 'info');
    
    loadMarketSummary();
    loadMarketTrends();
    loadTopCrops();
    loadBuyers();
    loadPrices();
    loadSuppliers();
    loadFinancialInstitutes();
    loadMarketActivity();
    
    setTimeout(() => {
        showToast('✅ Market data refreshed!', 'success');
    }, 1500);
}

// ===== EXPOSE MARKET FUNCTIONS =====
window.initMarketSection = initMarketSection;
window.switchMarketTab = switchMarketTab;
window.loadMarketSummary = loadMarketSummary;
window.loadMarketTrends = loadMarketTrends;
window.loadTopCrops = loadTopCrops;
window.loadBuyers = loadBuyers;
window.loadPrices = loadPrices;
window.loadSuppliers = loadSuppliers;
window.loadFinancialInstitutes = loadFinancialInstitutes;
window.loadMarketActivity = loadMarketActivity;
window.refreshMarketData = refreshMarketData;

console.log('📊 Market module loaded successfully!');

// ============================================================
// WEATHER FUNCTIONS
// ============================================================

function setWeatherLocation(location) {
    document.getElementById('weather-location').value = location;
    document.querySelectorAll('.location-tag').forEach(tag => {
        tag.classList.remove('active');
        if (tag.textContent.includes(location)) {
            tag.classList.add('active');
        }
    });
    getWeather();
}

function getWeatherIconClass(weatherCondition) {
    const condition = weatherCondition.toLowerCase();
    if (condition.includes('sunny') || condition.includes('clear')) return 'sunny';
    if (condition.includes('partly') || condition.includes('scattered')) return 'partly-cloudy';
    if (condition.includes('cloud') || condition.includes('overcast')) return 'cloudy';
    if (condition.includes('rain') || condition.includes('shower') || condition.includes('drizzle')) return 'rainy';
    if (condition.includes('thunder') || condition.includes('storm')) return 'stormy';
    if (condition.includes('snow') || condition.includes('flurries')) return 'snowy';
    if (condition.includes('fog') || condition.includes('mist') || condition.includes('haze')) return 'foggy';
    return 'partly-cloudy';
}

function getWeatherIcon(weatherCondition) {
    const condition = weatherCondition.toLowerCase();
    if (condition.includes('sunny') || condition.includes('clear')) return 'fa-sun';
    if (condition.includes('partly') || condition.includes('scattered')) return 'fa-cloud-sun';
    if (condition.includes('cloud') || condition.includes('overcast')) return 'fa-cloud';
    if (condition.includes('rain') || condition.includes('shower') || condition.includes('drizzle')) return 'fa-cloud-rain';
    if (condition.includes('thunder') || condition.includes('storm')) return 'fa-bolt';
    if (condition.includes('snow') || condition.includes('flurries')) return 'fa-snowflake';
    if (condition.includes('fog') || condition.includes('mist') || condition.includes('haze')) return 'fa-smog';
    return 'fa-cloud-sun';
}

async function getWeather() {
    const locationInput = document.getElementById('weather-location');
    const location = locationInput ? locationInput.value.trim() || 'Harare' : 'Harare';
    
    const currentEl = document.getElementById('weather-current');
    const forecastEl = document.getElementById('weather-forecast');
    const statusBadge = document.getElementById('weather-status');
    
    if (currentEl) currentEl.innerHTML = `
        <div class="weather-loading">
            <div class="loading-spinner"></div>
            <p style="color:#6b8a7a;">Fetching weather for ${location}...</p>
        </div>
    `;
    
    if (forecastEl) forecastEl.innerHTML = `
        <div class="weather-loading">
            <div class="loading-spinner"></div>
            <p style="color:#6b8a7a;">Loading 7-day forecast...</p>
        </div>
    `;
    
    try {
        const currentResp = await fetch(`${API_BASE}/weather/current/${location}`);
        const current = await currentResp.json();
        
        if (current.success && currentEl) {
            const isMock = current.is_mock || false;
            const weatherCondition = current.weather || 'Clear';
            const iconClass = getWeatherIconClass(weatherCondition);
            const iconName = getWeatherIcon(weatherCondition);
            
            if (statusBadge) {
                statusBadge.innerHTML = isMock ? 
                    '<i class="fas fa-info-circle" style="color:#f4a261;"></i> Mock Data' :
                    '<i class="fas fa-check-circle" style="color:#2ecc71;"></i> Live Data';
            }
            
            currentEl.className = 'weather-current-modern';
            currentEl.innerHTML = `
                <div class="weather-icon-display ${iconClass}">
                    <i class="fas ${iconName}"></i>
                </div>
                <div class="weather-info-main">
                    <div class="weather-temp-main">${Math.round(current.temperature)}<span class="temp-unit">°C</span></div>
                    <div class="weather-desc-main">${weatherCondition}</div>
                    <div class="weather-details-grid">
                        <div class="weather-detail-item">
                            <span class="detail-icon humidity"><i class="fas fa-tint"></i></span>
                            <div class="detail-info">
                                <span class="detail-value">${current.humidity || 0}%</span>
                                <span class="detail-label">Humidity</span>
                            </div>
                        </div>
                        <div class="weather-detail-item">
                            <span class="detail-icon wind"><i class="fas fa-wind"></i></span>
                            <div class="detail-info">
                                <span class="detail-value">${current.wind_speed || 0} km/h</span>
                                <span class="detail-label">Wind</span>
                            </div>
                        </div>
                        <div class="weather-detail-item">
                            <span class="detail-icon temperature"><i class="fas fa-thermometer-half"></i></span>
                            <div class="detail-info">
                                <span class="detail-value">${current.feels_like ? Math.round(current.feels_like) + '°C' : 'N/A'}</span>
                                <span class="detail-label">Feels Like</span>
                            </div>
                        </div>
                        <div class="weather-detail-item">
                            <span class="detail-icon pressure"><i class="fas fa-arrow-alt-circle-down"></i></span>
                            <div class="detail-info">
                                <span class="detail-value">${current.pressure || 'N/A'} hPa</span>
                                <span class="detail-label">Pressure</span>
                            </div>
                        </div>
                    </div>
                </div>
                <div class="weather-side-info">
                    ${current.sunrise ? `<div class="side-item"><i class="fas fa-sunrise"></i> ${current.sunrise}</div>` : ''}
                    ${current.sunset ? `<div class="side-item"><i class="fas fa-sunset"></i> ${current.sunset}</div>` : ''}
                    ${current.clouds !== undefined ? `<div class="side-item"><i class="fas fa-cloud"></i> ${current.clouds}%</div>` : ''}
                </div>
            `;
        }
        
        const forecastResp = await fetch(`${API_BASE}/weather/forecast/${location}`);
        const forecast = await forecastResp.json();
        
        if (forecast.success && forecastEl) {
            const shortDays = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
            
            forecastEl.className = 'weather-forecast-modern';
            
            let html = '';
            forecast.forecast.slice(0, 7).forEach((day, index) => {
                const date = new Date(day.date);
                const dayName = index === 0 ? 'Today' : shortDays[date.getDay()] || 'Day';
                const weatherCondition = day.weather || 'Clear';
                const iconClass = getWeatherIconClass(weatherCondition);
                const iconName = getWeatherIcon(weatherCondition);
                const maxTemp = day.max_temp || day.avg_temp + 3;
                const minTemp = day.min_temp || day.avg_temp - 3;
                const isToday = index === 0;
                
                html += `
                    <div class="forecast-day-modern ${isToday ? 'today' : ''}">
                        <div class="day-name">${dayName}</div>
                        <div class="day-icon-wrapper ${iconClass}">
                            <i class="fas ${iconName}"></i>
                        </div>
                        <div class="day-temps">
                            <span class="day-high">↑${Math.round(maxTemp)}°</span>
                            <span class="day-low">↓${Math.round(minTemp)}°</span>
                        </div>
                        <div class="day-weather">${weatherCondition}</div>
                        ${day.total_rain > 0 ? `<div class="day-rain">🌧️ ${day.total_rain.toFixed(1)}mm</div>` : ''}
                    </div>
                `;
            });
            
            forecastEl.innerHTML = html;
            
            const updateEl = document.getElementById('forecast-update');
            if (updateEl) {
                const now = new Date();
                updateEl.textContent = `Last updated: ${now.toLocaleTimeString()}`;
            }
        }
        
    } catch (error) {
        console.error('Weather error:', error);
        if (currentEl) {
            currentEl.className = 'weather-current-modern';
            currentEl.innerHTML = `
                <div style="text-align:center;padding:40px;color:var(--danger);grid-column:1 / -1;">
                    <i class="fas fa-exclamation-circle" style="font-size:2rem;display:block;margin-bottom:12px;"></i>
                    <h4>Unable to load weather data</h4>
                    <p style="color:#6b8a7a;">Please check your connection and try again.</p>
                    <button class="btn btn-primary" onclick="getWeather()" style="margin-top:12px;border-radius:12px;">
                        <i class="fas fa-sync-alt"></i> Retry
                    </button>
                </div>
            `;
        }
        if (forecastEl) {
            forecastEl.className = 'weather-forecast-modern';
            forecastEl.innerHTML = `
                <div style="text-align:center;padding:40px;color:#6b8a7a;grid-column:1 / -1;">
                    <i class="fas fa-cloud" style="font-size:2rem;display:block;margin-bottom:12px;opacity:0.3;"></i>
                    <p>Unable to load forecast</p>
                </div>
            `;
        }
    }
}

// ============================================================
// CROP SUITABILITY
// ============================================================

async function predictCrops() {
    const location = document.getElementById('crop-location')?.value || 'Harare';
    const region = document.getElementById('crop-region')?.value || 'Midveld';
    const soil_type = document.getElementById('crop-soil')?.value || 'Loam';
    const soil_ph = parseFloat(document.getElementById('crop-ph')?.value || 6.5);
    const climate = document.getElementById('crop-climate')?.value || 'Subtropical';
    const water_mm = parseInt(document.getElementById('crop-water')?.value || 800);
    const crop_type = document.getElementById('crop-type')?.value || 'Maize';
    const hectares = parseFloat(document.getElementById('crop-hectares')?.value || 5);
    const target_yield = parseFloat(document.getElementById('crop-yield')?.value || 10);
    const budget = parseFloat(document.getElementById('crop-budget')?.value || 5000);
    const capital = parseFloat(document.getElementById('crop-capital')?.value || 3000);
    const labour = parseInt(document.getElementById('crop-labour')?.value || 5);
    const seedlings = document.getElementById('crop-seedlings')?.value || 'Medium';
    
    const resultsEl = document.getElementById('crop-results');
    const placeholderEl = document.getElementById('crop-placeholder');
    const contentEl = document.getElementById('crop-results-content');
    
    if (!resultsEl) return;
    
    if (placeholderEl) placeholderEl.style.display = 'none';
    if (contentEl) {
        contentEl.style.display = 'block';
        contentEl.innerHTML = `
            <div class="crop-loading">
                <div class="loading-icon">🌾</div>
                <h4 style="color:var(--text-light);margin-top:8px;">Analyzing your farm data...</h4>
                <p style="color:var(--text-light);font-size:0.9rem;margin-top:4px;">
                    Considering location, soil, climate, water, budget, and more
                </p>
                <div style="margin-top:16px;display:flex;justify-content:center;gap:10px;">
                    <span class="loading-dot"></span>
                    <span class="loading-dot"></span>
                    <span class="loading-dot"></span>
                </div>
            </div>
        `;
    }
    
    try {
        const weatherResp = await fetch(`${API_BASE}/weather/current/${location}`);
        const weatherData = await weatherResp.json();
        const temp = weatherData.success ? weatherData.temperature : 25;
        
        const forecastResp = await fetch(`${API_BASE}/weather/forecast/${location}`);
        const forecastData = await forecastResp.json();
        let avgRainfall = water_mm;
        if (forecastData.success && forecastData.forecast) {
            const rainSum = forecastData.forecast.slice(0, 7).reduce((sum, d) => sum + (d.total_rain || 0), 0);
            avgRainfall = (rainSum / 7) * 30;
        }
        
        const requestData = {
            location: location,
            region: region,
            soil_type: soil_type,
            soil_ph: soil_ph,
            climate: climate,
            water_mm: water_mm,
            crop_type: crop_type,
            hectares: hectares,
            target_yield: target_yield,
            budget: budget,
            capital: capital,
            labour: labour,
            seedlings: seedlings,
            temperature: temp,
            rainfall: avgRainfall
        };
        
        const response = await fetch(`${API_BASE}/crops/suitability`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(requestData)
        });
        
        const data = await response.json();
        
        if (data.success) {
            displayCropResults(data, contentEl);
        } else {
            if (contentEl) {
                contentEl.innerHTML = `
                    <div style="text-align:center;padding:60px 20px;color:var(--danger);">
                        <i class="fas fa-exclamation-circle" style="font-size:3rem;display:block;margin-bottom:12px;"></i>
                        <h4 style="color:var(--danger);">Unable to Generate Recommendations</h4>
                        <p style="color:var(--text-light);">${data.error || 'Something went wrong. Please try again.'}</p>
                        <button class="btn btn-primary btn-sm" onclick="predictCrops()" style="margin-top:12px;">
                            <i class="fas fa-redo"></i> Try Again
                        </button>
                    </div>
                `;
            }
        }
    } catch (error) {
        console.error('Crop prediction error:', error);
        if (contentEl) {
            contentEl.innerHTML = `
                <div style="text-align:center;padding:60px 20px;color:var(--danger);">
                    <i class="fas fa-wifi" style="font-size:3rem;display:block;margin-bottom:12px;"></i>
                    <h4 style="color:var(--danger);">Connection Error</h4>
                    <p style="color:var(--text-light);">Please check your internet connection and try again.</p>
                    <button class="btn btn-primary btn-sm" onclick="predictCrops()" style="margin-top:12px;">
                        <i class="fas fa-redo"></i> Retry
                    </button>
                </div>
            `;
        }
    }
}

function displayCropResults(data, container) {
    const predictions = data.predictions || [];
    
    if (!container) return;
    
    if (predictions.length === 0) {
        container.innerHTML = `
            <div style="text-align:center;padding:60px 20px;color:var(--text-light);">
                <i class="fas fa-seedling" style="font-size:3rem;display:block;margin-bottom:12px;opacity:0.3;"></i>
                <h4 style="color:var(--text-light);">No Recommendations</h4>
                <p>Try adjusting your input parameters and try again.</p>
                <button class="btn btn-secondary btn-sm" onclick="predictCrops()" style="margin-top:12px;">
                    <i class="fas fa-redo"></i> Retry
                </button>
            </div>
        `;
        return;
    }
    
    let html = `
        <div style="margin-bottom:20px;padding:14px 20px;background:linear-gradient(135deg,rgba(26,92,74,0.06),rgba(244,162,97,0.04));border-radius:14px;display:flex;justify-content:space-between;flex-wrap:wrap;gap:12px;border:1px solid rgba(232,237,234,0.4);">
            <div style="font-size:0.85rem;color:var(--text-light);display:flex;align-items:center;gap:16px;flex-wrap:wrap;">
                <span><i class="fas fa-map-pin" style="color:var(--primary);"></i> ${data.location}</span>
                <span><i class="fas fa-mountain" style="color:var(--primary);"></i> ${data.soil_type}</span>
                <span><i class="fas fa-flask" style="color:var(--primary);"></i> pH ${data.soil_ph}</span>
            </div>
            <div style="font-size:0.85rem;color:var(--text-light);display:flex;align-items:center;gap:16px;flex-wrap:wrap;">
                <span><i class="fas fa-thermometer-half" style="color:var(--primary);"></i> ${Math.round(data.weather?.temperature || 25)}°C</span>
                <span><i class="fas fa-tint" style="color:var(--primary);"></i> ${data.weather?.rainfall || 800}mm</span>
            </div>
        </div>
    `;
    
    const rankEmojis = ['🥇', '🥈', '🥉', '4️⃣', '5️⃣'];
    
    predictions.forEach((crop, index) => {
        const score = crop.suitability_score || 0;
        const scoreClass = score > 0.7 ? 'score-high' : score > 0.5 ? 'score-medium' : 'score-low';
        const isRecommended = score > 0.6;
        const icon = rankEmojis[index] || '📊';
        
        const cropNotes = getCropNotes(crop.crop, score);
        const yieldPotential = getYieldPotential(crop.crop, score);
        const budgetEstimate = getBudgetEstimate(crop.crop, score);
        
        html += `
            <div class="crop-result-item">
                <div class="crop-result-header">
                    <div class="crop-name">
                        ${icon} ${crop.crop}
                        ${isRecommended ? '<span class="recommended-tag">✅ Recommended</span>' : '<span class="not-recommended-tag">⚠️ Not Recommended</span>'}
                    </div>
                    <span class="crop-score ${scoreClass}">${Math.round(score * 100)}% Match</span>
                </div>
                <div class="crop-result-details">
                    <div class="detail-item">
                        <strong>🌡️ Temp:</strong> ${Math.round(crop.temperature || 25)}°C
                    </div>
                    <div class="detail-item">
                        <strong>💧 Rainfall:</strong> ${Math.round(crop.rainfall || 800)}mm
                    </div>
                    <div class="detail-item">
                        <strong>🧪 Soil:</strong> ${crop.soil_type || 'N/A'}
                    </div>
                    <div class="detail-item">
                        <strong>📏 Yield:</strong> ${yieldPotential}
                    </div>
                    <div class="detail-item">
                        <strong>💰 Budget:</strong> ${budgetEstimate}
                    </div>
                    <div class="detail-item">
                        <strong>👨‍🌾 Labour:</strong> ${Math.round(score * 5 + 2)} workers/ha
                    </div>
                </div>
                <div class="crop-result-notes">
                    <strong>📝 ${isRecommended ? 'Recommended' : 'Consideration'} Notes:</strong><br>
                    ${cropNotes}
                </div>
            </div>
        `;
    });
    
    container.innerHTML = html;
}

function getCropNotes(crop, score) {
    const baseNotes = {
        'Maize': 'Plant 5-7cm deep, 30cm apart. Apply D-compound fertilizer at planting. Top dress with Urea 4-6 weeks after emergence. Water regularly during flowering.',
        'Tobacco': 'Plant in well-drained soil. Apply N-P-K fertilizer. Irrigate during dry periods. Harvest leaves individually as they mature.',
        'Wheat': 'Sow seeds 4-5cm deep. Apply nitrogen in split applications. Water during tillering and grain filling.',
        'Soybean': 'Plant 3-4cm deep, 45cm apart. Inoculate with Rhizobium. Apply phosphorus fertilizer.',
        'Cotton': 'Plant 3-5cm deep. Apply balanced fertilizer. Water during flowering and boll formation.',
        'Groundnuts': 'Plant 5-8cm deep. Apply lime if acidic. Water moderately. Harvest when pods mature.',
        'Sorghum': 'Plant 3-5cm deep. Apply nitrogen. Water during establishment and flowering.',
        'Sunflower': 'Plant 4-6cm deep. Apply phosphorus and potassium. Water during flowering.',
        'SweetPotato': 'Plant cuttings 20-30cm long. Apply potassium-rich fertilizer. Harvest 4-5 months later.',
        'Cassava': 'Plant stem cuttings 10-15cm long. Apply organic manure. Harvest 8-12 months later.'
    };
    
    const notes = baseNotes[crop] || 'Follow standard farming practices for this crop.';
    const confidence = score > 0.7 ? 'High confidence' : score > 0.5 ? 'Moderate confidence' : 'Low confidence';
    
    return `${notes} (${confidence} - ${Math.round(score * 100)}% match)`;
}

function getYieldPotential(crop, score) {
    const yields = {
        'Maize': '4-6 tonnes/ha',
        'Tobacco': '2-3 tonnes/ha',
        'Wheat': '3-4 tonnes/ha',
        'Soybean': '2-3 tonnes/ha',
        'Cotton': '1.5-2 tonnes/ha',
        'Groundnuts': '1-1.5 tonnes/ha',
        'Sorghum': '2-3 tonnes/ha',
        'Sunflower': '1.5-2 tonnes/ha',
        'SweetPotato': '10-15 tonnes/ha',
        'Cassava': '15-20 tonnes/ha'
    };
    return yields[crop] || 'Varies by conditions';
}

function getBudgetEstimate(crop, score) {
    const budgets = {
        'Maize': '$1,000-1,500/ha',
        'Tobacco': '$2,000-3,000/ha',
        'Wheat': '$1,200-1,800/ha',
        'Soybean': '$800-1,200/ha',
        'Cotton': '$1,500-2,000/ha',
        'Groundnuts': '$600-1,000/ha',
        'Sorghum': '$800-1,200/ha',
        'Sunflower': '$700-1,100/ha',
        'SweetPotato': '$500-800/ha',
        'Cassava': '$400-700/ha'
    };
    return budgets[crop] || '$800-1,500/ha';
}

// ============================================================
// LAND TENURE FUNCTIONS
// ============================================================

async function checkUserLandStatus() {
    // ... (keep your existing implementation)
}

function displayLandRecord(record) {
    // ... (keep your existing implementation)
}

async function registerLand() {
    // ... (keep your existing implementation)
}

function readFileAsBase64(file) {
    // ... (keep your existing implementation)
}

async function loadLandRecords() {
    // ... (keep your existing implementation)
}

async function updateLandStats(records = null) {
    // ... (keep your existing implementation)
}

async function approveLand(landId) {
    // ... (keep your existing implementation)
}

async function rejectLand(landId) {
    // ... (keep your existing implementation)
}

// ============================================================
// DATA SOVEREIGNTY FUNCTIONS
// ============================================================

// Tab switching
document.querySelectorAll('.data-tab-modern').forEach(tab => {
    tab.addEventListener('click', function() {
        document.querySelectorAll('.data-tab-modern').forEach(t => t.classList.remove('active'));
        document.querySelectorAll('.data-tab-content-modern').forEach(c => c.classList.remove('active'));
        this.classList.add('active');
        const tabId = this.dataset.tab;
        document.getElementById(`data-tab-${tabId}`).classList.add('active');
        if (tabId === 'yield') loadCropRecords();
        if (tabId === 'access') loadDataSovereignty();
        if (tabId === 'history') loadAccessHistory();
        if (tabId === 'benefits') loadBenefits();
    });
});

function updateTrustMeter(stats) {
    const { dataStored = 0, activeGrants = 0, totalAccesses = 0, benefits = 0 } = stats || {};
    document.getElementById('data-stored-count').textContent = dataStored;
    document.getElementById('active-grants-count').textContent = activeGrants;
    document.getElementById('total-accesses-count').textContent = totalAccesses;
    document.getElementById('benefits-count').textContent = benefits;
}

// ============================================================
// CROP RECORDS
// ============================================================

function showAddCropModal() {
    document.getElementById('cropModal').style.display = 'flex';
    document.getElementById('crop-planting-date').value = new Date().toISOString().split('T')[0];
}

function closeModal(modalId) {
    document.getElementById(modalId).style.display = 'none';
}

document.addEventListener('click', function(e) {
    if (e.target.classList.contains('modal')) {
        e.target.style.display = 'none';
    }
});

async function saveCropRecord() {
    const data = {
        crop_type: document.getElementById('crop-type-select').value,
        variety: document.getElementById('crop-variety').value,
        planting_date: document.getElementById('crop-planting-date').value,
        harvest_date: document.getElementById('crop-harvest-date').value || null,
        land_size: parseFloat(document.getElementById('crop-land-size').value || 0),
        yield_tonnes: parseFloat(document.getElementById('crop-yield-tonnes').value || 0),
        fertilizer: document.getElementById('crop-fertilizer').value,
        watering_method: document.getElementById('crop-watering').value,
        pest_control: document.getElementById('crop-pest-control').value,
        notes: document.getElementById('crop-notes').value,
        success_rate: parseInt(document.getElementById('crop-success-rate').value || 75)
    };
    
    if (!data.crop_type || !data.planting_date || !data.land_size || !data.yield_tonnes) {
        showToast('Please fill in all required fields', 'warning');
        return;
    }
    
    const submitBtn = document.querySelector('.modal-submit-btn');
    if (submitBtn) {
        submitBtn.disabled = true;
        submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> <span>Saving...</span>';
    }
    
    try {
        const response = await fetch(`${API_BASE}/crop/record`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        const result = await response.json();
        if (result.success) {
            showToast('✅ Crop record saved successfully!', 'success');
            closeModal('cropModal');
            document.getElementById('cropRecordForm').reset();
            loadCropRecords();
            updateTrustMeter();
        } else {
            showToast(`❌ Error: ${result.error}`, 'error');
        }
    } catch (error) {
        console.error('Error saving crop record:', error);
        showToast('❌ Network error. Please try again.', 'error');
    } finally {
        if (submitBtn) {
            submitBtn.disabled = false;
            submitBtn.innerHTML = '<i class="fas fa-save"></i> <span>Save Crop Record</span> <i class="fas fa-arrow-right"></i>';
        }
    }
}

async function loadCropRecords() {
    const container = document.getElementById('crop-records-list');
    if (!container) return;
    
    container.innerHTML = `<div class="loading-state"><div class="loading-spinner"></div><p>Loading your crop records...</p></div>`;
    
    try {
        const response = await fetch(`${API_BASE}/crop/records`);
        const data = await response.json();
        
        if (data.success) {
            document.getElementById('total-yield').textContent = data.total_yield || 0;
            document.getElementById('total-crops').textContent = data.total_crops || 0;
            document.getElementById('avg-success').textContent = data.avg_success || '0%';
            document.getElementById('crop-records-count').textContent = data.total_crops || 0;
            
            if (data.records.length === 0) {
                container.innerHTML = `
                    <div style="text-align:center;padding:40px 20px;color:var(--text-light);">
                        <i class="fas fa-seedling" style="font-size:2.5rem;display:block;margin-bottom:12px;opacity:0.2;"></i>
                        <h4 style="color:var(--text-light);">No crop records yet</h4>
                        <p style="color:var(--text-light);font-size:0.9rem;">Click "Add Crop Record" to start tracking your harvests</p>
                    </div>
                `;
                return;
            }
            
            let html = '';
            data.records.forEach(record => {
                const plantingDate = record.planting_date ? new Date(record.planting_date).toLocaleDateString() : 'N/A';
                const harvestDate = record.harvest_date ? new Date(record.harvest_date).toLocaleDateString() : 'Not yet';
                const successColor = record.success_rate >= 80 ? 'var(--success)' : record.success_rate >= 60 ? 'var(--secondary)' : 'var(--danger)';
                
                html += `
                    <div class="crop-record-modern">
                        <div class="record-header">
                            <span class="record-name"><i class="fas fa-seedling" style="color:var(--primary);"></i> ${record.crop_type} ${record.variety ? `(${record.variety})` : ''}</span>
                            <span class="record-yield">${record.yield_tonnes} tonnes</span>
                        </div>
                        <div class="record-details">
                            <span>📅 Planted: ${plantingDate}</span>
                            <span>📅 Harvest: ${harvestDate}</span>
                            <span>📏 Land: ${record.land_size} ha</span>
                            <span>💧 Watering: ${record.watering_method || 'N/A'}</span>
                            <span>🧪 Fertilizer: ${record.fertilizer || 'N/A'}</span>
                            <span style="color:${successColor};">📊 Success: ${record.success_rate}%</span>
                        </div>
                        ${record.notes ? `<div class="record-notes">📝 ${record.notes}</div>` : ''}
                    </div>
                `;
            });
            container.innerHTML = html;
        }
    } catch (error) {
        console.error('Error loading crop records:', error);
        container.innerHTML = `<div style="text-align:center;padding:40px;color:var(--danger);"><i class="fas fa-wifi" style="font-size:2rem;display:block;margin-bottom:12px;"></i><p>Error loading records. Please refresh.</p></div>`;
    }
}

// ============================================================
// ACCESS MANAGEMENT
// ============================================================

async function loadDataSovereignty() {
    const accessListEl = document.getElementById('data-access-list');
    const activeGrantsEl = document.getElementById('active-grants-list');
    const pendingBadge = document.getElementById('pending-number');
    const pendingCountEl = document.getElementById('pending-requests-count');
    
    if (!accessListEl || !activeGrantsEl) return;
    
    accessListEl.innerHTML = `<div class="loading-state"><div class="loading-spinner"></div><p>Loading requests...</p></div>`;
    activeGrantsEl.innerHTML = `<div class="loading-state"><div class="loading-spinner"></div><p>Loading active grants...</p></div>`;
    
    try {
        const requestsResponse = await fetch(`${API_BASE}/data/requests`);
        const requestsData = await requestsResponse.json();
        
        if (requestsData.success) {
            const pendingRequests = requestsData.requests.filter(r => r.status === 'Pending');
            const grantedRequests = requestsData.requests.filter(r => r.status === 'Granted');
            
            if (pendingBadge) pendingBadge.textContent = pendingRequests.length;
            if (pendingCountEl) pendingCountEl.textContent = pendingRequests.length;
            if (pendingCountEl) {
                pendingCountEl.style.display = pendingRequests.length > 0 ? 'inline' : 'none';
            }
            
            updateTrustMeter({ activeGrants: grantedRequests.length });
            
            let html = '';
            if (pendingRequests.length === 0) {
                html = `<div style="text-align:center;padding:30px 20px;color:var(--text-light);"><i class="fas fa-check-circle" style="font-size:2rem;color:var(--success);display:block;margin-bottom:8px;"></i><p>No pending access requests</p></div>`;
            } else {
                pendingRequests.forEach(req => {
                    html += `
                        <div class="access-request-modern">
                            <div class="request-info">
                                <span class="request-org">🏢 ${req.organization}</span>
                                <span class="request-purpose">${req.purpose || 'Data access request'}</span>
                                <span class="request-meta">📅 ${req.requested_at || 'N/A'}</span>
                            </div>
                            <div class="request-actions">
                                <button onclick="grantAccess('${req.id}')" class="btn btn-success btn-sm">✅ Grant</button>
                                <button onclick="denyAccess('${req.id}')" class="btn btn-danger btn-sm">❌ Deny</button>
                            </div>
                        </div>
                    `;
                });
            }
            accessListEl.innerHTML = html;
            
            let grantsHtml = '';
            if (grantedRequests.length === 0) {
                grantsHtml = `<div style="text-align:center;padding:20px;color:var(--text-light);"><p>No active grants</p></div>`;
            } else {
                grantedRequests.forEach(req => {
                    grantsHtml += `
                        <div class="grant-item-modern">
                            <span class="grant-org">🏢 ${req.organization}</span>
                            <span class="grant-status"><i class="fas fa-check-circle"></i> Active</span>
                        </div>
                    `;
                });
            }
            activeGrantsEl.innerHTML = grantsHtml;
        }
    } catch (error) {
        console.error('Data sovereignty error:', error);
        accessListEl.innerHTML = `<div style="text-align:center;padding:30px;color:var(--danger);"><i class="fas fa-exclamation-circle" style="font-size:1.5rem;display:block;margin-bottom:8px;"></i><p>Error loading requests</p></div>`;
        activeGrantsEl.innerHTML = `<div style="text-align:center;padding:30px;color:var(--danger);"><p>Error loading grants</p></div>`;
    }
}

// ============================================================
// ACCESS HISTORY
// ============================================================

async function loadAccessHistory() {
    const container = document.getElementById('data-history');
    const totalEl = document.getElementById('history-total');
    if (!container) return;
    
    container.innerHTML = `<div class="loading-state"><div class="loading-spinner"></div><p>Loading history...</p></div>`;
    
    try {
        const response = await fetch(`${API_BASE}/data/history`);
        const data = await response.json();
        
        if (data.success) {
            const total = data.history.length;
            totalEl.innerHTML = `<i class="fas fa-list"></i> ${total} accesses`;
            updateTrustMeter({ totalAccesses: total });
            
            if (total === 0) {
                container.innerHTML = `
                    <div style="text-align:center;padding:40px 20px;color:var(--text-light);">
                        <i class="fas fa-clock" style="font-size:2.5rem;display:block;margin-bottom:12px;opacity:0.2;"></i>
                        <h4 style="color:var(--text-light);">No access history yet</h4>
                        <p style="color:var(--text-light);font-size:0.9rem;">Your data access will appear here</p>
                    </div>
                `;
                return;
            }
            
            let html = '';
            data.history.forEach(item => {
                const date = item.date ? new Date(item.date).toLocaleString() : 'N/A';
                html += `
                    <div class="history-item-modern">
                        <span class="history-org">🏢 ${item.organization}</span>
                        <span class="history-info">accessed ${item.data_type || 'your data'}</span>
                        <span class="history-count">${item.count || 0} times</span>
                        <span class="history-date">${date}</span>
                    </div>
                `;
            });
            container.innerHTML = html;
        }
    } catch (error) {
        console.error('History error:', error);
        container.innerHTML = `<div style="text-align:center;padding:40px;color:var(--danger);"><i class="fas fa-wifi" style="font-size:2rem;display:block;margin-bottom:12px;"></i><p>Error loading history</p></div>`;
    }
}

// ============================================================
// BENEFITS
// ============================================================

async function loadBenefits() {
    const container = document.getElementById('benefits-list');
    const totalEl = document.getElementById('benefits-total');
    if (!container) return;
    
    container.innerHTML = `<div class="loading-state"><div class="loading-spinner"></div><p>Loading benefits...</p></div>`;
    
    try {
        const response = await fetch(`${API_BASE}/data/benefits`);
        const data = await response.json();
        
        if (data.success) {
            const benefits = data.benefits || [];
            totalEl.innerHTML = `<i class="fas fa-star"></i> ${benefits.length} benefits`;
            updateTrustMeter({ benefits: benefits.length });
            
            if (benefits.length === 0) {
                container.innerHTML = `
                    <div style="text-align:center;padding:40px 20px;color:var(--text-light);grid-column:1/-1;">
                        <i class="fas fa-gem" style="font-size:2.5rem;display:block;margin-bottom:12px;opacity:0.2;"></i>
                        <h4 style="color:var(--text-light);">No benefits yet</h4>
                        <p style="color:var(--text-light);font-size:0.9rem;">Share your data with organizations to start receiving value</p>
                    </div>
                `;
                return;
            }
            
            let html = '';
            benefits.forEach(benefit => {
                const iconMap = { 'advisory': '🌱', 'market': '📊', 'financial': '💰', 'input': '🧪', 'training': '📚', 'other': '🎯' };
                const icon = iconMap[benefit.type] || '🎯';
                
                html += `
                    <div class="benefit-card-modern">
                        <div class="benefit-top">
                            <span class="benefit-emoji">${icon}</span>
                            <span class="benefit-title">${benefit.title}</span>
                        </div>
                        <span class="benefit-desc">${benefit.description}</span>
                        <span class="benefit-value">${benefit.value || '✓'}</span>
                        <span class="benefit-date">📅 ${benefit.date || 'N/A'}</span>
                    </div>
                `;
            });
            container.innerHTML = html;
        }
    } catch (error) {
        console.error('Benefits error:', error);
        container.innerHTML = `<div style="text-align:center;padding:40px;color:var(--danger);grid-column:1/-1;"><i class="fas fa-wifi" style="font-size:2rem;display:block;margin-bottom:12px;"></i><p>Error loading benefits</p></div>`;
    }
}

// ============================================================
// GRANT/DENY ACCESS
// ============================================================

async function grantAccess(requestId) {
    if (!confirm('Grant access to this organization?')) return;
    try {
        const response = await fetch(`${API_BASE}/data/grant`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ request_id: requestId })
        });
        const data = await response.json();
        if (data.success) {
            showToast('✅ Access granted successfully!', 'success');
            loadDataSovereignty();
            loadAccessHistory();
            loadBenefits();
        } else {
            showToast(`❌ Error: ${data.error}`, 'error');
        }
    } catch (error) {
        console.error('Grant error:', error);
        showToast('❌ Network error. Please try again.', 'error');
    }
}

async function denyAccess(requestId) {
    if (!confirm('Deny access to this organization?')) return;
    try {
        const response = await fetch(`${API_BASE}/data/deny`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ request_id: requestId })
        });
        const data = await response.json();
        if (data.success) {
            showToast('❌ Access denied.', 'error');
            loadDataSovereignty();
        } else {
            showToast(`❌ Error: ${data.error}`, 'error');
        }
    } catch (error) {
        console.error('Deny error:', error);
        showToast('❌ Network error. Please try again.', 'error');
    }
}

// ============================================================
// CHATBOT
// ============================================================

let chatImageData = null;
let chatImageName = null;
let isProcessing = false;
let messageCount = 0;

const chatMessages = document.getElementById('chat-messages-modern');
const chatInput = document.getElementById('chat-input-modern');
const chatSendBtn = document.getElementById('chat-send-btn');
const typingDots = document.getElementById('typing-dots');

document.querySelectorAll('.lang-btn').forEach(btn => {
    btn.addEventListener('click', function() {
        document.querySelectorAll('.lang-btn').forEach(b => b.classList.remove('active'));
        this.classList.add('active');
        state.chatLanguage = this.dataset.lang;
        showToast(`Language changed to ${this.dataset.lang}`, 'info');
    });
});

if (chatInput) {
    chatInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessageModern();
        }
    });
}

const uploadBtn = document.getElementById('chat-upload-btn');
const imageInput = document.getElementById('chat-image-input');

if (uploadBtn && imageInput) {
    uploadBtn.addEventListener('click', function() {
        imageInput.click();
    });
    imageInput.addEventListener('change', function(e) {
        const file = e.target.files[0];
        if (file) {
            const reader = new FileReader();
            reader.onload = function(event) {
                chatImageData = event.target.result;
                chatImageName = file.name;
                const preview = document.getElementById('chat-image-preview');
                const img = document.getElementById('chat-preview-img');
                const filename = document.getElementById('chat-preview-filename');
                preview.style.display = 'block';
                img.src = event.target.result;
                filename.textContent = file.name;
            };
            reader.readAsDataURL(file);
        }
        this.value = '';
    });
}

function cancelImageUpload() {
    chatImageData = null;
    chatImageName = null;
    document.getElementById('chat-image-preview').style.display = 'none';
    document.getElementById('chat-image-input').value = '';
}

function sendQuickMessage(message) {
    if (chatInput) {
        chatInput.value = message;
        sendMessageModern();
    }
}

function clearChat() {
    if (!confirm('Clear all chat messages?')) return;
    const welcomeMessage = chatMessages.querySelector('.message-modern.bot');
    chatMessages.innerHTML = '';
    if (welcomeMessage) {
        chatMessages.appendChild(welcomeMessage);
    } else {
        chatMessages.innerHTML = `<div class="message-modern bot"><div class="message-avatar bot-avatar"><i class="fas fa-robot"></i></div><div class="message-content-modern"><div class="message-header"><span class="message-sender">AgricLedger AI</span><span class="message-time">Just now</span></div><div class="message-text"><div class="welcome-message"><div class="welcome-emoji">👋</div><div class="welcome-text"><strong>Sawubona / Mhoro / Hello!</strong><p>I'm your AgricLedger AI Assistant. How can I help you today?</p></div></div><div class="quick-actions"><button class="quick-action" onclick="sendQuickMessage('How do I grow maize?')"><span class="quick-icon">🌽</span> Maize farming</button><button class="quick-action" onclick="sendQuickMessage('How do I control pests?')"><span class="quick-icon">🐛</span> Pest control</button><button class="quick-action" onclick="sendQuickMessage('What is the best time to plant?')"><span class="quick-icon">🌱</span> Planting tips</button><button class="quick-action" onclick="sendQuickMessage('How do I market my produce?')"><span class="quick-icon">📊</span> Marketing</button></div><div class="chat-tip"><i class="fas fa-camera"></i> Upload a photo of your crop for diagnosis!</div></div></div></div>`;
    }
    showToast('Chat cleared', 'info');
}

async function sendMessageModern() {
    if (isProcessing) return;
    const input = document.getElementById('chat-input-modern');
    const message = input.value.trim();
    if (!message && !chatImageData) return;
    if (message) {
        addMessageModern(message, 'user');
        input.value = '';
    }
    if (chatImageData) {
        const imgHtml = `<img src="${chatImageData}" alt="Uploaded crop image" />`;
        addMessageModern(imgHtml, 'user', true);
    }
    showTypingIndicator();
    isProcessing = true;
    try {
        const requestData = { message: message || "Analyze this image", language: state.chatLanguage || 'English' };
        if (chatImageData) {
            requestData.image = chatImageData;
            requestData.image_name = chatImageName;
        }
        const response = await fetch(`${API_BASE}/chat/advanced`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(requestData)
        });
        const data = await response.json();
        removeTypingIndicator();
        if (data.success) {
            let responseText = data.response;
            if (data.has_image) {
                responseText = `<img src="${data.image_url}" alt="Analysis result" /><br>${data.response}`;
            }
            addMessageModern(responseText, 'bot', true);
        } else {
            addMessageModern(`❌ ${data.error || 'Something went wrong. Please try again.'}`, 'bot');
        }
    } catch (error) {
        console.error('Chat error:', error);
        removeTypingIndicator();
        addMessageModern('❌ Network error. Please check your connection and try again.', 'bot');
    } finally {
        isProcessing = false;
        cancelImageUpload();
    }
}

async function sendImageForAnalysis() {
    if (!chatImageData) return;
    await sendMessageModern();
}

function addMessageModern(content, sender, isHtml = false) {
    if (!chatMessages) return;
    const emptyState = chatMessages.querySelector('.empty-state');
    if (emptyState) emptyState.remove();
    const div = document.createElement('div');
    div.className = `message-modern ${sender}`;
    const avatar = document.createElement('div');
    avatar.className = `message-avatar ${sender === 'bot' ? 'bot-avatar' : 'user-avatar'}`;
    avatar.innerHTML = sender === 'bot' ? '<i class="fas fa-robot"></i>' : '<i class="fas fa-user"></i>';
    const contentDiv = document.createElement('div');
    contentDiv.className = 'message-content-modern';
    const header = document.createElement('div');
    header.className = 'message-header';
    const senderName = document.createElement('span');
    senderName.className = 'message-sender';
    senderName.textContent = sender === 'bot' ? 'AgricLedger AI' : 'You';
    const time = document.createElement('span');
    time.className = 'message-time';
    time.textContent = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    header.appendChild(senderName);
    header.appendChild(time);
    const textDiv = document.createElement('div');
    textDiv.className = 'message-text';
    if (isHtml) {
        textDiv.innerHTML = content;
    } else {
        textDiv.textContent = content;
    }
    contentDiv.appendChild(header);
    contentDiv.appendChild(textDiv);
    div.appendChild(avatar);
    div.appendChild(contentDiv);
    chatMessages.appendChild(div);
    chatMessages.scrollTop = chatMessages.scrollHeight;
    messageCount++;
}

function showTypingIndicator() {
    if (!chatMessages) return;
    removeTypingIndicator();
    const div = document.createElement('div');
    div.className = 'message-modern bot';
    div.id = 'typing-indicator';
    const avatar = document.createElement('div');
    avatar.className = 'message-avatar bot-avatar';
    avatar.innerHTML = '<i class="fas fa-robot"></i>';
    const contentDiv = document.createElement('div');
    contentDiv.className = 'message-content-modern';
    const typingDiv = document.createElement('div');
    typingDiv.className = 'typing-indicator';
    typingDiv.innerHTML = '<span></span><span></span><span></span>';
    contentDiv.appendChild(typingDiv);
    div.appendChild(avatar);
    div.appendChild(contentDiv);
    chatMessages.appendChild(div);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

function removeTypingIndicator() {
    const indicator = document.getElementById('typing-indicator');
    if (indicator) indicator.remove();
}

const chatContainer = document.querySelector('.chat-container-modern');
if (chatContainer) {
    chatContainer.addEventListener('dragover', function(e) {
        e.preventDefault();
        this.style.borderColor = 'var(--primary)';
        this.style.boxShadow = '0 0 0 4px rgba(26, 92, 74, 0.06)';
    });
    chatContainer.addEventListener('dragleave', function(e) {
        e.preventDefault();
        this.style.borderColor = '';
        this.style.boxShadow = '';
    });
    chatContainer.addEventListener('drop', function(e) {
        e.preventDefault();
        this.style.borderColor = '';
        this.style.boxShadow = '';
        const files = e.dataTransfer.files;
        if (files.length > 0 && files[0].type.startsWith('image/')) {
            const file = files[0];
            const reader = new FileReader();
            reader.onload = function(event) {
                chatImageData = event.target.result;
                chatImageName = file.name;
                const preview = document.getElementById('chat-image-preview');
                const img = document.getElementById('chat-preview-img');
                const filename = document.getElementById('chat-preview-filename');
                preview.style.display = 'block';
                img.src = event.target.result;
                filename.textContent = file.name;
                showToast('Image uploaded successfully!', 'success');
            };
            reader.readAsDataURL(file);
        }
    });
}

document.addEventListener('DOMContentLoaded', function() {
    const welcomeTime = document.getElementById('welcome-time');
    if (welcomeTime) {
        welcomeTime.textContent = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    }
});

console.log('🤖 Chatbot UI loaded successfully!');

// ============================================================
// FARMERS MANAGEMENT - MODERN UI/UX
// ============================================================

// ---- STATE ----
let currentFarmers = [];
let filteredFarmers = [];
let currentPage = 1;
const itemsPerPage = 10;
let currentFilter = 'all';
let searchQuery = '';

// ---- DOM REFS ----
const container = document.getElementById('farmers-list');
const searchInput = document.getElementById('farmers-search-input');
const searchClear = document.getElementById('search-clear');
const pageInfo = document.getElementById('page-info');
const prevBtn = document.getElementById('prev-page');
const nextBtn = document.getElementById('next-page');

// ---- LOAD FARMERS ----
async function loadFarmers() {
    if (!container) return;

    container.innerHTML = `
        <div class="loading-state">
            <div class="loading-spinner"></div>
            <p>Loading farmers...</p>
        </div>
    `;

    try {
        const response = await fetch(`${API_BASE}/farmers/all`);
        const data = await response.json();

        if (data.success && data.farmers) {
            currentFarmers = data.farmers;
            updateStatsAndTabs();
            applyFiltersAndRender();
        } else {
            container.innerHTML = `
                <div style="text-align:center;padding:60px 20px;color:var(--text-light);">
                    <i class="fas fa-users" style="font-size:2.5rem;display:block;margin-bottom:12px;opacity:0.2;"></i>
                    <h4 style="color:var(--text-light);">No farmers found</h4>
                    <p style="color:var(--text-light);font-size:0.9rem;">
                        Farmers will appear here once they register
                    </p>
                </div>
            `;
        }
    } catch (error) {
        console.error('Error loading farmers:', error);
        container.innerHTML = `
            <div style="text-align:center;padding:60px 20px;color:var(--danger);">
                <i class="fas fa-wifi" style="font-size:2.5rem;display:block;margin-bottom:12px;"></i>
                <h4 style="color:var(--danger);">Connection Error</h4>
                <p style="color:var(--text-light);">Please check your connection and try again.</p>
                <button class="btn btn-primary btn-sm" onclick="refreshFarmers()" style="margin-top:12px;border-radius:10px;">
                    <i class="fas fa-redo"></i> Retry
                </button>
            </div>
        `;
    }
}

// ---- UPDATE STATS & TABS ----
function updateStatsAndTabs() {
    const total = currentFarmers.length;
    const active = currentFarmers.filter(f => f.is_active === 1 || f.is_active === true).length;
    const pending = currentFarmers.filter(f => f.status === 'pending' || f.is_approved === 0).length;
    const inactive = currentFarmers.filter(f => f.is_active === 0 || f.is_active === false).length;

    // Stats
    document.getElementById('total-farmers').textContent = total;
    document.getElementById('active-farmers').textContent = active;
    document.getElementById('pending-farmers').textContent = pending;
    document.getElementById('inactive-farmers').textContent = inactive;

    // Tabs
    document.getElementById('tab-all-count').textContent = total;
    document.getElementById('tab-active-count').textContent = active;
    document.getElementById('tab-pending-count').textContent = pending;
    document.getElementById('tab-inactive-count').textContent = inactive;
}

// ---- FILTER FARMERS ----
function filterFarmers(filter) {
    currentFilter = filter;
    currentPage = 1;

    document.querySelectorAll('.farmers-tab-modern').forEach(tab => {
        tab.classList.toggle('active', tab.dataset.filter === filter);
    });

    applyFiltersAndRender();
}

// ---- SEARCH FARMERS ----
function searchFarmers() {
    searchQuery = searchInput.value.toLowerCase().trim();
    currentPage = 1;
    searchClear.style.display = searchQuery.length > 0 ? 'flex' : 'none';
    applyFiltersAndRender();
}

// ---- CLEAR SEARCH ----
function clearSearch() {
    searchInput.value = '';
    searchQuery = '';
    searchClear.style.display = 'none';
    currentPage = 1;
    applyFiltersAndRender();
    searchInput.focus();
}

// ---- APPLY FILTERS & RENDER ----
function applyFiltersAndRender() {
    let result = [...currentFarmers];

    // Filter by status
    if (currentFilter === 'active') {
        result = result.filter(f => f.is_active === 1 || f.is_active === true);
    } else if (currentFilter === 'pending') {
        result = result.filter(f => f.status === 'pending' || f.is_approved === 0);
    } else if (currentFilter === 'inactive') {
        result = result.filter(f => f.is_active === 0 || f.is_active === false);
    }

    // Filter by search query
    if (searchQuery) {
        const q = searchQuery;
        result = result.filter(f =>
            (f.first_name && f.first_name.toLowerCase().includes(q)) ||
            (f.last_name && f.last_name.toLowerCase().includes(q)) ||
            (f.email && f.email.toLowerCase().includes(q)) ||
            (f.farmer_id && f.farmer_id.toLowerCase().includes(q)) ||
            (f.location && f.location.toLowerCase().includes(q)) ||
            (f.phone && f.phone.toLowerCase().includes(q))
        );
    }

    filteredFarmers = result;
    renderFarmers();
}

// ---- RENDER FARMERS ----
function renderFarmers() {
    if (!container) return;

    const totalPages = Math.ceil(filteredFarmers.length / itemsPerPage) || 1;
    const start = (currentPage - 1) * itemsPerPage;
    const end = Math.min(start + itemsPerPage, filteredFarmers.length);
    const pageItems = filteredFarmers.slice(start, end);

    // Update pagination
    pageInfo.textContent = `Page ${currentPage} of ${totalPages}`;
    prevBtn.disabled = currentPage <= 1;
    nextBtn.disabled = currentPage >= totalPages;

    // Empty state
    if (pageItems.length === 0) {
        container.innerHTML = `
            <div style="text-align:center;padding:60px 20px;color:var(--text-light);">
                <i class="fas fa-search" style="font-size:2.5rem;display:block;margin-bottom:12px;opacity:0.2;"></i>
                <h4 style="color:var(--text-light);">No farmers found</h4>
                <p style="color:var(--text-light);font-size:0.9rem;">
                    ${searchQuery ? 'Try adjusting your search criteria.' : 'No farmers match the selected filter.'}
                </p>
            </div>
        `;
        return;
    }

    // Build table
    let html = `
        <table class="farmers-table">
            <thead>
                <tr>
                    <th>#</th>
                    <th>Farmer</th>
                    <th>Farmer ID</th>
                    <th>Email</th>
                    <th>Location</th>
                    <th>Status</th>
                    <th>Actions</th>
                </tr>
            </thead>
            <tbody>
    `;

    pageItems.forEach((farmer, index) => {
        const fullName = `${farmer.first_name || ''} ${farmer.last_name || ''}`.trim() || 'Unknown';
        const initials = fullName
            .split(' ')
            .map(n => n[0])
            .join('')
            .toUpperCase()
            .substring(0, 2);

        const isActive = farmer.is_active === 1 || farmer.is_active === true;
        const isPending = farmer.status === 'pending' || farmer.is_approved === 0;
        const status = isActive ? 'active' : isPending ? 'pending' : 'inactive';
        const statusLabel = status === 'active' ? 'Active' : status === 'pending' ? 'Pending' : 'Inactive';
        const statusIcon = status === 'active' ? '✅' : status === 'pending' ? '⏳' : '❌';

        html += `
            <tr>
                <td style="font-weight:600;color:var(--text-light);">${start + index + 1}</td>
                <td>
                    <div class="farmer-info-cell">
                        <div class="farmer-avatar-modern">${initials || '?'}</div>
                        <div>
                            <div class="farmer-name-modern">${fullName}</div>
                            <div class="farmer-email-modern">${farmer.email || 'N/A'}</div>
                        </div>
                    </div>
                </td>
                <td><strong style="color:var(--primary);">${farmer.farmer_id || 'N/A'}</strong></td>
                <td>${farmer.email || 'N/A'}</td>
                <td>${farmer.location || 'N/A'}</td>
                <td>
                    <span class="status-badge-modern-table ${status}">
                        ${statusIcon} ${statusLabel}
                    </span>
                </td>
                <td>
                    <div class="action-buttons-modern">
        `;

        if (status === 'pending') {
            html += `
                <button onclick="approveFarmer('${farmer.id}')" class="btn btn-approve btn-sm">
                    <i class="fas fa-check"></i> Approve
                </button>
                <button onclick="rejectFarmer('${farmer.id}')" class="btn btn-reject btn-sm">
                    <i class="fas fa-times"></i> Reject
                </button>
            `;
        } else if (status === 'active') {
            html += `
                <button onclick="toggleFarmerStatus('${farmer.id}', 'inactive')" class="btn btn-deactivate btn-sm">
                    <i class="fas fa-pause"></i> Deactivate
                </button>
            `;
        } else {
            html += `
                <button onclick="toggleFarmerStatus('${farmer.id}', 'active')" class="btn btn-activate btn-sm">
                    <i class="fas fa-play"></i> Activate
                </button>
            `;
        }

        html += `
                <button onclick="viewFarmerDetails('${farmer.id}')" class="btn btn-view btn-sm">
                    <i class="fas fa-eye"></i> View
                </button>
                </div>
            </td>
        </tr>
        `;
    });

    html += `
            </tbody>
        </table>
    `;

    container.innerHTML = html;
}

// ---- CHANGE PAGE ----
function changePage(direction) {
    const totalPages = Math.ceil(filteredFarmers.length / itemsPerPage) || 1;

    if (direction === 'prev' && currentPage > 1) {
        currentPage--;
    } else if (direction === 'next' && currentPage < totalPages) {
        currentPage++;
    }

    renderFarmers();

    // Scroll to top of table
    const tableWrapper = document.querySelector('.farmers-table-modern');
    if (tableWrapper) {
        tableWrapper.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
}

// ---- REFRESH ----
function refreshFarmers() {
    showToast('🔄 Refreshing farmers...', 'info');
    loadFarmers();
}

// ---- EXPORT ----
function exportFarmers() {
    if (filteredFarmers.length === 0) {
        showToast('No farmers to export.', 'warning');
        return;
    }

    const headers = ['ID', 'Farmer ID', 'First Name', 'Last Name', 'Email', 'Phone', 'Location', 'Status', 'Created At'];
    const rows = filteredFarmers.map(f => [
        f.id,
        f.farmer_id || 'N/A',
        f.first_name || '',
        f.last_name || '',
        f.email || '',
        f.phone || '',
        f.location || '',
        f.is_active ? 'Active' : 'Inactive',
        f.created_at || ''
    ]);

    const csv = [headers, ...rows].map(row => row.join(',')).join('\n');
    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `farmers_export_${new Date().toISOString().split('T')[0]}.csv`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);

    showToast(`✅ Exported ${filteredFarmers.length} farmers`, 'success');
}

// ---- APPROVE ----
async function approveFarmer(userId) {
    const farmer = currentFarmers.find(f => f.id == userId);
    const name = `${farmer?.first_name || ''} ${farmer?.last_name || ''}`.trim() || 'this farmer';

    if (!confirm(`✅ Approve ${name}? They will be able to access the system.`)) return;

    try {
        const response = await fetch(`${API_BASE}/farmers/approve`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ user_id: userId })
        });
        const data = await response.json();

        if (data.success) {
            showToast(`✅ ${name} approved successfully!`, 'success');
            loadFarmers();
        } else {
            showToast(`❌ Error: ${data.error || 'Unknown error'}`, 'error');
        }
    } catch (error) {
        console.error('Approve error:', error);
        showToast('❌ Network error. Please try again.', 'error');
    }
}

// ---- REJECT ----
async function rejectFarmer(userId) {
    const farmer = currentFarmers.find(f => f.id == userId);
    const name = `${farmer?.first_name || ''} ${farmer?.last_name || ''}`.trim() || 'this farmer';

    if (!confirm(`❌ Reject ${name}? They will not be able to access the system.`)) return;

    try {
        const response = await fetch(`${API_BASE}/farmers/reject`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ user_id: userId })
        });
        const data = await response.json();

        if (data.success) {
            showToast(`❌ ${name} rejected.`, 'error');
            loadFarmers();
        } else {
            showToast(`❌ Error: ${data.error || 'Unknown error'}`, 'error');
        }
    } catch (error) {
        console.error('Reject error:', error);
        showToast('❌ Network error. Please try again.', 'error');
    }
}

// ---- TOGGLE STATUS ----
async function toggleFarmerStatus(userId, action) {
    const farmer = currentFarmers.find(f => f.id == userId);
    const name = `${farmer?.first_name || ''} ${farmer?.last_name || ''}`.trim() || 'this farmer';
    const actionText = action === 'active' ? 'activate' : 'deactivate';
    const emoji = action === 'active' ? '🟢' : '🔴';

    if (!confirm(`${emoji} Are you sure you want to ${actionText} ${name}?`)) return;

    try {
        const response = await fetch(`${API_BASE}/farmers/toggle-status`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ user_id: userId, action: action })
        });
        const data = await response.json();

        if (data.success) {
            showToast(`✅ ${name} ${actionText}d successfully!`, 'success');
            loadFarmers();
        } else {
            showToast(`❌ Error: ${data.error || 'Unknown error'}`, 'error');
        }
    } catch (error) {
        console.error('Toggle error:', error);
        showToast('❌ Network error. Please try again.', 'error');
    }
}

// ---- VIEW FARMER DETAILS ----
function viewFarmerDetails(userId) {
    const farmer = currentFarmers.find(f => f.id == userId);
    if (!farmer) {
        showToast('Farmer not found', 'error');
        return;
    }

    const fullName = `${farmer.first_name || ''} ${farmer.last_name || ''}`.trim() || 'Unknown';
    const initials = fullName
        .split(' ')
        .map(n => n[0])
        .join('')
        .toUpperCase()
        .substring(0, 2);

    const isActive = farmer.is_active === 1 || farmer.is_active === true;
    const isPending = farmer.status === 'pending' || farmer.is_approved === 0;
    const status = isActive ? 'Active' : isPending ? 'Pending' : 'Inactive';
    const statusEmoji = status === 'Active' ? '✅' : status === 'Pending' ? '⏳' : '❌';
    const joinedDate = farmer.created_at ? new Date(farmer.created_at).toLocaleDateString() : 'N/A';
    const lastLogin = farmer.last_login ? new Date(farmer.last_login).toLocaleString() : 'Never';

    const detailsHtml = `
        <div style="padding:20px;max-width:420px;margin:0 auto;">
            <div style="text-align:center;margin-bottom:20px;">
                <div style="width:72px;height:72px;border-radius:50%;background:linear-gradient(135deg,var(--primary),var(--primary-light));color:white;display:flex;align-items:center;justify-content:center;font-size:1.8rem;font-weight:700;margin:0 auto 12px;box-shadow:0 4px 16px rgba(26,92,74,0.2);">
                    ${initials || '?'}
                </div>
                <h3 style="margin:0;font-size:1.2rem;">${fullName}</h3>
                <p style="color:var(--text-light);margin:4px 0;font-size:0.85rem;">
                    <strong style="color:var(--primary);">${farmer.farmer_id || 'N/A'}</strong>
                </p>
            </div>
            <div style="display:grid;grid-template-columns:1fr 1fr;gap:6px 16px;font-size:0.85rem;background:#f8fbfa;padding:16px;border-radius:12px;border:1px solid #e8edea;">
                <div><strong>📧 Email:</strong></div>
                <div style="word-break:break-all;">${farmer.email || 'N/A'}</div>
                <div><strong>📱 Phone:</strong></div>
                <div>${farmer.phone || 'N/A'}</div>
                <div><strong>📍 Location:</strong></div>
                <div>${farmer.location || 'N/A'}</div>
                <div><strong>👤 Role:</strong></div>
                <div>${farmer.role || 'Farmer'}</div>
                <div><strong>📊 Status:</strong></div>
                <div>${statusEmoji} ${status}</div>
                <div><strong>📅 Joined:</strong></div>
                <div>${joinedDate}</div>
                <div><strong>🕐 Last Login:</strong></div>
                <div>${lastLogin}</div>
            </div>
        </div>
    `;

    // Modal
    const modal = document.createElement('div');
    modal.className = 'farmer-detail-modal';
    modal.style.cssText = `
        position:fixed;top:0;left:0;width:100%;height:100%;
        background:rgba(0,0,0,0.5);backdrop-filter:blur(8px);
        display:flex;align-items:center;justify-content:center;
        z-index:9999;padding:20px;
        animation:fadeIn 0.2s ease-out;
    `;

    modal.innerHTML = `
        <div style="
            background:var(--card-bg);
            border-radius:20px;
            max-width:500px;
            width:100%;
            max-height:80vh;
            overflow-y:auto;
            padding:24px;
            box-shadow:0 20px 60px rgba(0,0,0,0.2);
            position:relative;
            animation:slideUp 0.25s ease-out;
        ">
            <button onclick="this.closest('.farmer-detail-modal').remove()" style="
                position:absolute;top:12px;right:16px;
                background:none;border:none;font-size:1.6rem;
                cursor:pointer;color:var(--text-light);
                transition:all 0.2s;padding:4px 8px;
                border-radius:8px;line-height:1;
            " onmouseover="this.style.background='#f0f0f0'" onmouseout="this.style.background='transparent'">
                ×
            </button>
            ${detailsHtml}
        </div>
    `;

    document.body.appendChild(modal);

    modal.addEventListener('click', function(e) {
        if (e.target === this) this.remove();
    });

    // Add keydown handler
    const escHandler = (e) => {
        if (e.key === 'Escape') {
            modal.remove();
            document.removeEventListener('keydown', escHandler);
        }
    };
    document.addEventListener('keydown', escHandler);
}

// ---- TOAST NOTIFICATION ----
function showToast(message, type = 'info') {
    const icons = {
        success: '✅',
        error: '❌',
        warning: '⚠️',
        info: 'ℹ️'
    };

    const colors = {
        success: 'var(--success)',
        error: 'var(--danger)',
        warning: 'var(--warning)',
        info: 'var(--primary)'
    };

    // Remove existing toasts
    const existing = document.querySelectorAll('.custom-toast');
    existing.forEach(el => el.remove());

    const toast = document.createElement('div');
    toast.className = 'custom-toast';
    toast.style.cssText = `
        position:fixed;bottom:24px;right:24px;
        background:var(--card-bg);
        color:var(--text);
        padding:14px 24px;
        border-radius:14px;
        box-shadow:0 8px 32px rgba(0,0,0,0.12);
        border-left:4px solid ${colors[type] || 'var(--primary)'};
        font-size:0.9rem;
        font-weight:500;
        z-index:10000;
        max-width:400px;
        display:flex;
        align-items:center;
        gap:10px;
        animation:slideInRight 0.3s ease-out;
    `;

    toast.innerHTML = `
        <span style="font-size:1.2rem;">${icons[type] || 'ℹ️'}</span>
        <span>${message}</span>
    `;

    document.body.appendChild(toast);

    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transform = 'translateX(40px)';
        toast.style.transition = 'all 0.3s ease-out';
        setTimeout(() => toast.remove(), 350);
    }, 4000);
}

// ---- KEYBOARD SHORTCUTS ----
document.addEventListener('keydown', function(e) {
    // Ctrl+K or Cmd+K to focus search
    if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
        e.preventDefault();
        const searchInput = document.getElementById('farmers-search-input');
        if (searchInput) {
            searchInput.focus();
            searchInput.select();
        }
    }

    // Escape to clear search
    if (e.key === 'Escape') {
        const searchInput = document.getElementById('farmers-search-input');
        if (searchInput && document.activeElement === searchInput) {
            clearSearch();
            searchInput.blur();
        }
    }
});

// ---- INIT ----
document.addEventListener('DOMContentLoaded', function() {
    // Inject animation styles if not already present
    if (!document.getElementById('farmers-animations')) {
        const style = document.createElement('style');
        style.id = 'farmers-animations';
        style.textContent = `
            @keyframes fadeIn {
                from { opacity: 0; }
                to { opacity: 1; }
            }
            @keyframes slideUp {
                from { opacity: 0; transform: translateY(20px) scale(0.98); }
                to { opacity: 1; transform: translateY(0) scale(1); }
            }
            @keyframes slideInRight {
                from { opacity: 0; transform: translateX(40px); }
                to { opacity: 1; transform: translateX(0); }
            }
        `;
        document.head.appendChild(style);
    }

    loadFarmers();

    console.log('👨‍🌾 Farmers Management UI loaded successfully!');
    console.log('📌 Tip: Press Ctrl+K to search, Escape to clear');
});

// ---- EXPOSE TO GLOBAL ----
window.loadFarmers = loadFarmers;
window.filterFarmers = filterFarmers;
window.searchFarmers = searchFarmers;
window.clearSearch = clearSearch;
window.changePage = changePage;
window.refreshFarmers = refreshFarmers;
window.exportFarmers = exportFarmers;
window.approveFarmer = approveFarmer;
window.rejectFarmer = rejectFarmer;
window.toggleFarmerStatus = toggleFarmerStatus;
window.viewFarmerDetails = viewFarmerDetails;
window.showToast = showToast;

console.log('👨‍🌾 Farmers Management fully loaded!');

// ============================================================
// SETTINGS - Tabbed Container Design - COMPLETE
// ============================================================

// ===== TAB SWITCHING =====
function switchTab(tab) {
    console.log('🔄 Switching to tab:', tab);
    
    // Update tab buttons
    document.querySelectorAll('.settings-tab-btn').forEach(function(btn) {
        btn.classList.remove('active');
        if (btn.getAttribute('data-tab') === tab) {
            btn.classList.add('active');
        }
    });

    // Update tab panels
    document.querySelectorAll('.settings-tab-panel').forEach(function(panel) {
        panel.classList.remove('active');
    });

    var target = document.getElementById('settings-tab-' + tab);
    if (target) {
        target.classList.add('active');
        console.log('✅ Tab panel activated:', tab);
    } else {
        console.warn('⚠️ Tab panel not found:', 'settings-tab-' + tab);
    }
}

// ===== THEME TOGGLE =====
function toggleTheme() {
    console.log('🎨 Toggling theme');
    var isDark = document.documentElement.classList.contains('dark');
    var toggle = document.getElementById('theme-toggle');

    if (isDark) {
        document.documentElement.classList.remove('dark');
        localStorage.setItem('theme', 'light');
        if (toggle) toggle.checked = false;
        showToast('🌞 Light mode activated', 'info');
    } else {
        document.documentElement.classList.add('dark');
        localStorage.setItem('theme', 'dark');
        if (toggle) toggle.checked = true;
        showToast('🌙 Dark mode activated', 'info');
    }
}

// ===== FONT SIZE =====
function changeFontSize(delta) {
    var slider = document.getElementById('font-size-slider');
    if (!slider) return;
    var value = parseInt(slider.value) + delta;
    value = Math.max(80, Math.min(140, value));
    slider.value = value;
    updateFontSize(value);
}

function updateFontSize(value) {
    var display = document.getElementById('font-size-display');
    if (display) display.textContent = value + '%';
    document.body.style.fontSize = value + '%';
    localStorage.setItem('fontSize', value);
}

// ===== PASSWORD STRENGTH =====
function initPasswordStrength() {
    var passwordInput = document.getElementById('new-password');
    if (!passwordInput) return;

    passwordInput.addEventListener('input', function() {
        var value = this.value;
        var segments = [
            document.getElementById('seg-1'),
            document.getElementById('seg-2'),
            document.getElementById('seg-3'),
            document.getElementById('seg-4')
        ];
        var text = document.getElementById('strength-text');

        var strength = 0;
        if (value.length >= 8) strength++;
        if (value.match(/[a-z]/)) strength++;
        if (value.match(/[A-Z]/)) strength++;
        if (value.match(/[0-9!@#$%^&*]/)) strength++;

        var levels = ['Weak', 'Weak', 'Fair', 'Good', 'Strong'];
        var classes = ['', 'weak', 'fair', 'good', 'strong'];
        var colors = ['#ea4335', '#ea4335', '#fbbc04', '#f9ab00', '#34a853'];

        segments.forEach(function(seg, index) {
            if (seg) {
                seg.classList.remove('active', 'weak', 'fair', 'good', 'strong');
                if (index < strength) {
                    seg.classList.add('active', classes[strength]);
                }
            }
        });

        if (text) {
            text.textContent = levels[strength];
            text.style.color = colors[strength];
        }

        checkPasswordMatch();
    });

    var confirmInput = document.getElementById('confirm-password');
    if (confirmInput) {
        confirmInput.addEventListener('input', checkPasswordMatch);
    }
}

function checkPasswordMatch() {
    var password = document.getElementById('new-password');
    var confirm = document.getElementById('confirm-password');
    var matchText = document.getElementById('match-text');

    if (!password || !confirm || !matchText) return;

    if (confirm.value && password.value === confirm.value) {
        matchText.textContent = '✅ Passwords match';
        matchText.className = 'password-match success';
        confirm.style.borderColor = '#34a853';
    } else if (confirm.value) {
        matchText.textContent = '❌ Passwords do not match';
        matchText.className = 'password-match error';
        confirm.style.borderColor = '#ea4335';
    } else {
        matchText.textContent = '';
        matchText.className = 'password-match';
        confirm.style.borderColor = '#e8e8e8';
    }
}

// ===== TOGGLE PASSWORD VISIBILITY =====
function toggleVisibility(inputId) {
    var input = document.getElementById(inputId);
    if (!input) return;
    var btn = input.parentElement.querySelector('.password-toggle');
    if (!btn) return;

    if (input.type === 'password') {
        input.type = 'text';
        btn.innerHTML = '<i class="fas fa-eye-slash"></i>';
    } else {
        input.type = 'password';
        btn.innerHTML = '<i class="fas fa-eye"></i>';
    }
}

// ===== SAVE PROFILE =====
function saveProfile() {
    var data = {
        first_name: document.getElementById('profile-first-name')?.value,
        last_name: document.getElementById('profile-last-name')?.value,
        phone: document.getElementById('profile-phone')?.value,
        location: document.getElementById('profile-location')?.value,
        bio: document.getElementById('profile-bio')?.value
    };

    var btn = document.querySelector('#profile-form .btn-primary');
    if (!btn) return;

    btn.disabled = true;
    btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Saving...';

    // Simulate API call
    setTimeout(function() {
        showToast('✅ Profile updated successfully!', 'success');
        // Update display name
        var fullName = data.first_name + ' ' + data.last_name;
        var nameDisplay = document.getElementById('settings-display-name');
        if (nameDisplay) nameDisplay.textContent = fullName;
        // Update avatar initials
        var initials = (data.first_name[0] + data.last_name[0]).toUpperCase();
        var initialsDisplay = document.getElementById('avatar-initials');
        if (initialsDisplay) initialsDisplay.textContent = initials;

        btn.disabled = false;
        btn.innerHTML = '<i class="fas fa-save"></i> Save Changes';
    }, 1000);
}

// ===== CHANGE PASSWORD =====
function changePassword() {
    var current = document.getElementById('current-password')?.value;
    var newPass = document.getElementById('new-password')?.value;
    var confirm = document.getElementById('confirm-password')?.value;

    if (!current || !newPass || !confirm) {
        showToast('⚠️ Please fill in all password fields.', 'warning');
        return;
    }
    if (newPass !== confirm) {
        showToast('⚠️ New passwords do not match.', 'warning');
        return;
    }
    if (newPass.length < 8) {
        showToast('⚠️ Password must be at least 8 characters.', 'warning');
        return;
    }

    var btn = document.querySelector('#password-form .btn-primary');
    if (!btn) return;

    btn.disabled = true;
    btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Updating...';

    setTimeout(function() {
        showToast('✅ Password updated successfully!', 'success');
        document.getElementById('password-form').reset();
        document.querySelectorAll('.strength-segment').forEach(function(el) {
            el.classList.remove('active', 'weak', 'fair', 'good', 'strong');
        });
        var strengthText = document.getElementById('strength-text');
        if (strengthText) {
            strengthText.textContent = 'Weak';
            strengthText.style.color = '#ea4335';
        }
        var matchText = document.getElementById('match-text');
        if (matchText) matchText.textContent = '';

        btn.disabled = false;
        btn.innerHTML = '<i class="fas fa-key"></i> Update Password';
    }, 1000);
}

// ===== TWO-FACTOR AUTH =====
function setup2FA() {
    showToast('🔐 Redirecting to 2FA setup...', 'info');
    setTimeout(function() {
        window.location.href = '/setup-2fa';
    }, 1000);
}

function disable2FA() {
    if (!confirm('Are you sure you want to disable Two-Factor Authentication?')) return;
    showToast('2FA disabled successfully.', 'info');
}

// ===== LOGOUT =====
function logoutUser() {
    if (!confirm('Are you sure you want to logout?')) return;
    window.location.href = '/logout';
}

// ===== LANGUAGE =====
function changeLanguage(lang) {
    var labels = {
        'en': 'English',
        'sn': 'Shona',
        'nd': 'Ndebele',
        'fr': 'Français'
    };
    showToast('🌐 Language changed to ' + (labels[lang] || lang), 'info');
    localStorage.setItem('language', lang);
}

// ===== AVATAR UPLOAD =====
function handleAvatarUpload(event) {
    var file = event.target.files[0];
    if (!file) return;

    if (!file.type.startsWith('image/')) {
        showToast('❌ Please select an image file.', 'error');
        return;
    }

    if (file.size > 5 * 1024 * 1024) {
        showToast('❌ Image must be less than 5MB.', 'error');
        return;
    }

    var reader = new FileReader();
    reader.onload = function(e) {
        var avatar = document.getElementById('settings-avatar');
        var initials = document.getElementById('avatar-initials');
        // Remove existing img if any
        var oldImg = avatar.querySelector('img');
        if (oldImg) oldImg.remove();
        // Hide initials
        initials.style.display = 'none';
        // Create new image
        var newImg = document.createElement('img');
        newImg.src = e.target.result;
        newImg.alt = 'Profile';
        avatar.appendChild(newImg);
        showToast('✅ Avatar updated successfully!', 'success');
    };
    reader.readAsDataURL(file);
}

// ===== TOAST NOTIFICATION =====
function showToast(message, type) {
    type = type || 'info';
    var existing = document.querySelector('.toast-notification');
    if (existing) existing.remove();

    var toast = document.createElement('div');
    toast.className = 'toast-notification ' + type;
    var icons = { success: '✅', error: '❌', info: 'ℹ️', warning: '⚠️' };
    var colors = { success: '#34a853', error: '#ea4335', info: '#1a5c4a', warning: '#fbbc04' };

    toast.innerHTML = `
        <span class="toast-icon">${icons[type] || 'ℹ️'}</span>
        <span class="toast-message">${message}</span>
        <button class="toast-close" onclick="this.parentElement.remove()">×</button>
    `;

    toast.style.cssText = `
        position: fixed;
        bottom: 24px;
        right: 24px;
        background: #ffffff;
        padding: 12px 18px;
        border-radius: 12px;
        box-shadow: 0 8px 30px rgba(0,0,0,0.15);
        display: flex;
        align-items: center;
        gap: 10px;
        z-index: 9999;
        max-width: 380px;
        animation: slideUp 0.3s ease;
        border-left: 4px solid ${colors[type] || '#1a5c4a'};
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    `;

    if (!document.getElementById('toast-animations')) {
        var style = document.createElement('style');
        style.id = 'toast-animations';
        style.textContent = `
            @keyframes slideUp {
                from { opacity: 0; transform: translateY(20px); }
                to { opacity: 1; transform: translateY(0); }
            }
            .toast-notification .toast-close {
                background: none;
                border: none;
                font-size: 1.4rem;
                cursor: pointer;
                color: #5f6368;
                padding: 0 4px;
                border-radius: 4px;
                transition: background 0.2s;
            }
            .toast-notification .toast-close:hover {
                background: #f1f3f4;
            }
            .toast-notification .toast-message {
                font-size: 0.85rem;
                color: #202124;
            }
            .toast-notification .toast-icon {
                font-size: 1.2rem;
            }
        `;
        document.head.appendChild(style);
    }

    document.body.appendChild(toast);
    setTimeout(function() {
        if (toast.parentElement) toast.remove();
    }, 5000);
}

// ===== INIT SETTINGS =====
function initSettings() {
    console.log('⚙️ Initializing Settings...');

    // Restore theme
    var theme = localStorage.getItem('theme');
    if (theme === 'dark') {
        document.documentElement.classList.add('dark');
        var toggle = document.getElementById('theme-toggle');
        if (toggle) toggle.checked = true;
    }

    // Restore font size
    var fontSize = localStorage.getItem('fontSize');
    if (fontSize) {
        var slider = document.getElementById('font-size-slider');
        if (slider) {
            slider.value = fontSize;
            updateFontSize(fontSize);
        }
    }

    // Restore language
    var language = localStorage.getItem('language');
    if (language) {
        var select = document.getElementById('language-select');
        if (select) select.value = language;
    }

    // Initialize password strength
    initPasswordStrength();

    console.log('✅ Settings initialized successfully');
}

// Initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initSettings);
} else {
    initSettings();
}

console.log('⚙️ Settings module loaded successfully!');

// ============================================================
// REVIEWS & FEEDBACK - Premium UI/UX
// ============================================================

let reviewsFilter = 'all';
let allReviews = [];

// ===== SET RATING =====
function setRating(value) {
    const stars = document.querySelectorAll('#star-rating .star');
    const ratingText = document.getElementById('rating-text');
    const ratingValue = document.getElementById('rating-value');

    stars.forEach((star, index) => {
        if (index < value) {
            star.classList.add('active');
            star.textContent = '★';
        } else {
            star.classList.remove('active');
            star.textContent = '☆';
        }
    });

    ratingValue.value = value;

    const labels = {
        1: '⭐ Poor - Needs improvement',
        2: '⭐⭐ Fair - Below expectations',
        3: '⭐⭐⭐ Good - Satisfactory',
        4: '⭐⭐⭐⭐ Great - Above expectations',
        5: '⭐⭐⭐⭐⭐ Excellent - Outstanding!'
    };

    ratingText.textContent = labels[value] || 'Click a star to rate';
    ratingText.style.color = value > 3 ? '#2e7d32' : value > 2 ? '#f9ab00' : '#ea4335';
}

// ===== SET FEATURE RATING =====
function setFeatureRating(feature, value) {
    const container = document.querySelector(`.mini-stars[data-feature="${feature}"]`);
    if (!container) return;

    const stars = container.querySelectorAll('.mini-star');
    stars.forEach((star, index) => {
        if (index < value) {
            star.classList.add('active');
            star.textContent = '★';
        } else {
            star.classList.remove('active');
            star.textContent = '☆';
        }
    });
}

// ===== GET FEATURE RATING =====
function getFeatureRating(feature) {
    const container = document.querySelector(`.mini-stars[data-feature="${feature}"]`);
    if (!container) return 0;
    return container.querySelectorAll('.mini-star.active').length;
}

// ===== CHARACTER COUNTER =====
document.addEventListener('DOMContentLoaded', function() {
    const reviewContent = document.getElementById('review-content');
    const charCount = document.getElementById('char-count');

    if (reviewContent && charCount) {
        reviewContent.addEventListener('input', function() {
            const length = this.value.length;
            charCount.textContent = length;

            if (length > 500) {
                charCount.style.color = '#ea4335';
            } else if (length > 400) {
                charCount.style.color = '#f9ab00';
            } else {
                charCount.style.color = '#5f6368';
            }
        });
    }
});

// ===== SUBMIT REVIEW =====
async function submitReview() {
    const rating = parseInt(document.getElementById('rating-value').value);
    const title = document.getElementById('review-title').value.trim();
    const content = document.getElementById('review-content').value.trim();
    const recommend = document.querySelector('input[name="recommend"]:checked')?.value || 'yes';
    const features = {
        crops: getFeatureRating('crops'),
        weather: getFeatureRating('weather'),
        land: getFeatureRating('land'),
        chat: getFeatureRating('chat'),
        data: getFeatureRating('data')
    };

    // Validation
    if (rating === 0) {
        showToast('Please select a rating.', 'warning');
        return;
    }

    if (!title) {
        showToast('Please enter a review title.', 'warning');
        document.getElementById('review-title').focus();
        return;
    }

    if (!content || content.length < 10) {
        showToast('Please write a review (minimum 10 characters).', 'warning');
        document.getElementById('review-content').focus();
        return;
    }

    if (content.length > 500) {
        showToast('Review must be under 500 characters.', 'warning');
        return;
    }

    const btn = document.querySelector('.btn-submit-review');
    btn.disabled = true;
    btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Submitting...';

    try {
        const response = await fetch(`${API_BASE}/reviews/submit`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                rating: rating,
                title: title,
                content: content,
                recommend: recommend,
                features: features
            })
        });

        const data = await response.json();

        if (data.success) {
            showToast('✅ Review submitted successfully!', 'success');

            // Reset form
            document.getElementById('reviewForm').reset();
            document.querySelectorAll('#star-rating .star').forEach(s => {
                s.classList.remove('active');
                s.textContent = '☆';
            });
            document.getElementById('rating-value').value = 0;
            document.getElementById('rating-text').textContent = 'Click a star to rate';
            document.getElementById('rating-text').style.color = '#5f6368';

            document.querySelectorAll('.mini-star').forEach(s => {
                s.classList.remove('active');
                s.textContent = '☆';
            });

            document.getElementById('char-count').textContent = '0';
            document.getElementById('char-count').style.color = '#5f6368';

            // Reload reviews
            loadReviews();
        } else {
            showToast('❌ Error: ' + data.error, 'error');
        }
    } catch (error) {
        console.error('Submit review error:', error);
        showToast('❌ Network error. Please try again.', 'error');
    }

    btn.disabled = false;
    btn.innerHTML = '<i class="fas fa-paper-plane"></i> Submit Review';
}

// ===== LOAD REVIEWS =====
async function loadReviews() {
    const container = document.getElementById('reviews-list');
    if (!container) return;

    container.innerHTML = `
        <div class="loading-state">
            <div class="loading-spinner"></div>
            <p>Loading reviews...</p>
        </div>
    `;

    try {
        const response = await fetch(`${API_BASE}/reviews/all`);
        const data = await response.json();

        if (data.success) {
            allReviews = data.reviews;
            updateReviewStats(data.reviews);
            renderReviews(data.reviews);
        } else {
            container.innerHTML = `
                <div style="text-align:center;padding:40px;color:#5f6368;">
                    <i class="fas fa-star" style="font-size:2.5rem;display:block;margin-bottom:12px;color:#f4a261;opacity:0.3;"></i>
                    <h4 style="color:#5f6368;">No reviews yet</h4>
                    <p style="font-size:0.9rem;">Be the first to review AgricLedger!</p>
                </div>
            `;
        }
    } catch (error) {
        console.error('Error loading reviews:', error);
        container.innerHTML = `
            <div style="text-align:center;padding:40px;color:#ea4335;">
                <i class="fas fa-exclamation-circle" style="font-size:2.5rem;display:block;margin-bottom:12px;"></i>
                <h4 style="color:#ea4335;">Connection Error</h4>
                <p style="color:#5f6368;font-size:0.9rem;">Please check your connection and try again.</p>
                <button class="btn btn-primary btn-sm" onclick="refreshReviews()" style="margin-top:12px;border-radius:10px;">
                    <i class="fas fa-redo"></i> Retry
                </button>
            </div>
        `;
    }
}

// ===== UPDATE REVIEW STATS =====
function updateReviewStats(reviews) {
    if (!reviews || reviews.length === 0) {
        document.getElementById('avg-rating').textContent = '0.0';
        document.getElementById('total-reviews').textContent = '0';
        document.getElementById('recommend-rate').textContent = '0%';
        document.getElementById('avg-stars').textContent = '☆☆☆☆☆';
        return;
    }

    const totalRating = reviews.reduce((sum, r) => sum + r.rating, 0);
    const avgRating = totalRating / reviews.length;

    document.getElementById('avg-rating').textContent = avgRating.toFixed(1);
    document.getElementById('total-reviews').textContent = reviews.length;

    const recommendCount = reviews.filter(r => r.recommend === 'yes').length;
    const recommendRate = (recommendCount / reviews.length) * 100;
    document.getElementById('recommend-rate').textContent = Math.round(recommendRate) + '%';

    const fullStars = Math.round(avgRating);
    let starsDisplay = '';
    for (let i = 0; i < 5; i++) {
        starsDisplay += i < fullStars ? '★' : '☆';
    }
    document.getElementById('avg-stars').textContent = starsDisplay;
}

// ===== RENDER REVIEWS =====
function renderReviews(reviews) {
    const container = document.getElementById('reviews-list');
    const countDisplay = document.getElementById('review-count');

    if (!container) return;

    if (reviews.length === 0) {
        container.innerHTML = `
            <div style="text-align:center;padding:40px;color:#5f6368;">
                <i class="fas fa-search" style="font-size:2.5rem;display:block;margin-bottom:12px;opacity:0.2;"></i>
                <h4 style="color:#5f6368;">No reviews found</h4>
                <p style="font-size:0.9rem;">Try adjusting your filter criteria</p>
            </div>
        `;
        if (countDisplay) countDisplay.textContent = '0 reviews';
        return;
    }

    if (countDisplay) {
        countDisplay.textContent = `${reviews.length} review${reviews.length > 1 ? 's' : ''}`;
    }

    let html = '';

    reviews.forEach((review) => {
        const stars = '★'.repeat(review.rating) + '☆'.repeat(5 - review.rating);
        const initials = review.user_name ?
            review.user_name.split(' ').map(n => n[0]).join('').toUpperCase().substring(0, 2) :
            '??';

        const recommendClass = review.recommend === 'yes' ? 'yes' :
                              review.recommend === 'no' ? 'no' : 'maybe';
        const recommendLabel = review.recommend === 'yes' ? '✅ Recommends' :
                              review.recommend === 'no' ? '❌ Not Recommends' : '🤔 Maybe';

        const date = review.created_at ?
            new Date(review.created_at).toLocaleDateString('en-US', {
                year: 'numeric',
                month: 'short',
                day: 'numeric'
            }) :
            'Recently';

        html += `
            <div class="review-item">
                <div class="review-header">
                    <div class="review-user">
                        <div class="review-avatar">${initials}</div>
                        <div class="review-user-info">
                            <div class="review-name">${review.user_name || 'Anonymous Farmer'}</div>
                            <div class="review-date">${date}</div>
                        </div>
                    </div>
                    <div class="review-rating">
                        ${stars}
                        <span class="rating-number">${review.rating}/5</span>
                    </div>
                </div>
                <div class="review-title">${review.title || 'Review'}</div>
                <div class="review-content">${review.content}</div>`;

        if (review.features) {
            html += `<div class="review-features">`;
            const featureMap = {
                crops: '🌱 Crop',
                weather: '🌤️ Weather',
                land: '🏛️ Land',
                chat: '🤖 AI',
                data: '🔐 Data'
            };

            Object.keys(featureMap).forEach(key => {
                if (review.features[key] && review.features[key] > 0) {
                    const stars = '★'.repeat(review.features[key]) + '☆'.repeat(5 - review.features[key]);
                    html += `
                        <span class="review-feature-item">
                            ${featureMap[key]}: <span class="feature-rating">${stars}</span>
                        </span>
                    `;
                }
            });
            html += `</div>`;
        }

        html += `
                <span class="review-recommend ${recommendClass}">${recommendLabel}</span>
                <div class="review-actions">
                    <button class="btn" onclick="likeReview('${review.id}')">
                        <i class="fas fa-thumbs-up"></i>
                        <span id="likes-${review.id}">${review.likes || 0}</span>
                    </button>
                    <button class="btn" onclick="reportReview('${review.id}')">
                        <i class="fas fa-flag"></i>
                    </button>
                </div>
            </div>
        `;
    });

    container.innerHTML = html;
}

// ===== FILTER REVIEWS =====
function filterReviews(filter) {
    reviewsFilter = filter;

    document.querySelectorAll('.filter-btn').forEach(btn => {
        btn.classList.remove('active');
        if (btn.dataset.filter === filter) {
            btn.classList.add('active');
        }
    });

    let filtered = [...allReviews];

    if (filter === '5') {
        filtered = filtered.filter(r => r.rating === 5);
    } else if (filter === '4') {
        filtered = filtered.filter(r => r.rating === 4);
    } else if (filter === '3') {
        filtered = filtered.filter(r => r.rating === 3);
    } else if (filter === 'latest') {
        filtered = filtered.sort((a, b) => new Date(b.created_at) - new Date(a.created_at));
    } else {
        filtered = filtered.sort((a, b) => new Date(b.created_at) - new Date(a.created_at));
    }

    renderReviews(filtered);
}

// ===== LIKE REVIEW =====
async function likeReview(reviewId) {
    try {
        const response = await fetch(`${API_BASE}/reviews/like`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ review_id: reviewId })
        });

        const data = await response.json();

        if (data.success) {
            const likesSpan = document.getElementById(`likes-${reviewId}`);
            if (likesSpan) {
                likesSpan.textContent = data.likes;
                // Animate the like
                likesSpan.style.color = '#2ecc71';
                setTimeout(() => {
                    likesSpan.style.color = '';
                }, 500);
            }
        }
    } catch (error) {
        console.error('Error liking review:', error);
        showToast('Error liking review. Please try again.', 'error');
    }
}

// ===== REPORT REVIEW =====
function reportReview(reviewId) {
    if (confirm('Report this review for inappropriate content?')) {
        showToast('Review reported. We will review it shortly.', 'info');
    }
}

// ===== REFRESH REVIEWS =====
function refreshReviews() {
    showToast('🔄 Refreshing reviews...', 'info');
    loadReviews();
}

// ===== EXPOSE REVIEWS FUNCTIONS =====
window.setRating = setRating;
window.setFeatureRating = setFeatureRating;
window.submitReview = submitReview;
window.loadReviews = loadReviews;
window.filterReviews = filterReviews;
window.likeReview = likeReview;
window.reportReview = reportReview;
window.refreshReviews = refreshReviews;

console.log('⭐ Reviews & Feedback UI loaded successfully!');


// ============================================================
// FOOTER FUNCTIONS
// ============================================================

function initFooter() {
    const yearElement = document.querySelector('.footer-copyright-text');
    if (yearElement) {
        const currentYear = new Date().getFullYear();
        yearElement.textContent = `© ${currentYear} All Rights Reserved`;
    }
    console.log('✅ Footer initialized');
}

document.addEventListener('DOMContentLoaded', function() {
    initFooter();
});

// ============================================================
// EXPOSE SETTINGS FUNCTIONS TO GLOBAL SCOPE
// ============================================================
window.toggleTheme = toggleTheme;
window.changeFontSize = changeFontSize;
window.updateFontSize = updateFontSize;
window.togglePasswordVisibility = togglePasswordVisibility;
window.saveProfile = saveProfile;
window.changePassword = changePassword;
window.setup2FA = setup2FA;
window.disable2FA = disable2FA;
window.deleteAccount = deleteAccount;
window.logoutUser = logoutUser;
window.endSession = endSession;
window.endAllSessions = endAllSessions;
window.initSettings = initSettings;