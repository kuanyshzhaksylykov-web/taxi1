// Основной файл приложения для водителей

// Инициализация Vue.js приложения
const app = new Vue({
    el: '#app',
    data: {
        // Состояния экранов
        currentScreen: 'loading',
        
        // Данные пользователя
        phone: '',
        password: '',
        isAuthenticated: false,
        driverInfo: {},
        driverStats: {},
        driverRating: 5.0,
        
        // Состояние водителя
        driverStatus: 'offline', // 'offline', 'online', 'busy'
        statusText: 'Не на линии',
        balance: 0,
        onlineTime: 0,
        onlineTimer: null,
        
        // Заказы
        nearbyOrders: [],
        newOrder: null,
        currentOrder: null,
        orderTimer: 30,
        orderTimerInterval: null,
        
        // Текущая поездка
        rideStep: 1, // 1-4
        rideTimer: 0,
        rideTimerInterval: null,
        
        // Навигация
        activeTab: 'home',
        
        // Карта
        map: null,
        myLocationMarker: null,
        orderMarkers: [],
        route: null,
        trafficEnabled: false,
        
        // Регистрация
        regStep: 1,
        regData: {
            firstName: '',
            lastName: '',
            middleName: '',
            birthDate: '',
            carBrand: '',
            carModel: '',
            carYear: '',
            carColor: '',
            carPlate: '',
            licenseNumber: '',
            licenseExpiry: '',
            insuranceNumber: '',
            insuranceExpiry: '',
            documents: {
                license_front: null,
                license_back: null,
                insurance: null,
                car_front: null
            },
            agreeTerms: false
        },
        
        // Проблемы
        problemTypes: [
            { id: 1, name: 'Проблема с пассажиром', icon: 'fas fa-user-times' },
            { id: 2, name: 'Проблема с автомобилем', icon: 'fas fa-car-crash' },
            { id: 3, name: 'ДТП', icon: 'fas fa-car-burst' },
            { id: 4, name: 'Проблема с оплатой', icon: 'fas fa-credit-card' },
            { id: 5, name: 'Другое', icon: 'fas fa-question-circle' }
        ],
        selectedProblem: null,
        problemDescription: '',
        
        // Уведомления
        unreadNotifications: 0,
        notifications: [],
        
        // Статистика
        todayStats: {
            rides: 0,
            earnings: 0,
            hours: 0
        },
        
        // WebSocket
        ws: null,
        wsConnected: false,
        
        // API конфигурация
        apiUrl: 'http://localhost:8000/api',
        wsUrl: 'ws://localhost:8000/ws',
        
        // Telegram WebApp
        tg: null,
        tgInitialized: false
    },
    computed: {
        // Вычисляемые свойства
        rideIcon() {
            switch(this.rideStep) {
                case 1: return 'fa-car';
                case 2: return 'fa-user-check';
                case 3: return 'fa-route';
                case 4: return 'fa-flag-checkered';
                default: return 'fa-car';
            }
        },
        
        rideStatusText() {
            switch(this.rideStep) {
                case 1: return 'Еду к пассажиру';
                case 2: return 'Пассажир в машине';
                case 3: return 'Еду к точке Б';
                case 4: return 'Завершить поездку';
                default: return 'Поездка';
            }
        }
    },
    mounted() {
        // Инициализация приложения
        this.initApp();
    },
    methods: {
        // ======================
        // ИНИЦИАЛИЗАЦИЯ
        // ======================
        
        async initApp() {
            console.log('Инициализация приложения...');
            
            try {
                // 1. Проверка Telegram WebApp
                if (window.Telegram && window.Telegram.WebApp) {
                    this.tg = Telegram.WebApp;
                    this.tg.expand();
                    this.tgInitialized = true;
                    console.log('Telegram WebApp инициализирован');
                }
                
                // 2. Проверка авторизации
                const token = localStorage.getItem('driver_token');
                if (token) {
                    // Проверяем валидность токена
                    const isValid = await this.validateToken(token);
                    if (isValid) {
                        this.isAuthenticated = true;
                        await this.loadDriverData();
                        this.showMainScreen();
                        return;
                    } else {
                        localStorage.removeItem('driver_token');
                    }
                }
                
                // 3. Показываем экран авторизации
                this.showLoginScreen();
                
            } catch (error) {
                console.error('Ошибка инициализации:', error);
                this.showLoginScreen();
            }
        },
        
        async validateToken(token) {
            // Проверка токена через API
            try {
                const response = await axios.get(`${this.apiUrl}/drivers/me`, {
                    headers: { 'Authorization': `Bearer ${token}` }
                });
                return response.data.success;
            } catch (error) {
                return false;
            }
        },
        
        // ======================
        // АВТОРИЗАЦИЯ
        // ======================
        
        showLoginScreen() {
            this.hideAllScreens();
            document.getElementById('login-screen').style.display = 'block';
            this.currentScreen = 'login';
        },
        
        showRegistrationScreen() {
            this.hideAllScreens();
            document.getElementById('registration-screen').style.display = 'block';
            this.currentScreen = 'registration';
        },
        
        showMainScreen() {
            this.hideAllScreens();
            document.getElementById('main-screen').style.display = 'block';
            this.currentScreen = 'main';
            
            // Инициализируем карту
            this.initMap();
            
            // Запускаем обновление геолокации
            this.startLocationUpdates();
            
            // Подключаемся к WebSocket
            this.connectWebSocket();
            
            // Загружаем данные
            this.loadNearbyOrders();
        },
        
        showProfileScreen() {
            this.hideAllScreens();
            document.getElementById('profile-screen').style.display = 'block';
            this.currentScreen = 'profile';
        },
        
        hideAllScreens() {
            const screens = document.querySelectorAll('.screen');
            screens.forEach(screen => {
                screen.style.display = 'none';
            });
        },
        
        async login() {
            if (!this.phone || !this.password) {
                this.showNotification('error', 'Ошибка', 'Заполните все поля');
                return;
            }
            
            try {
                // В реальном приложении здесь запрос к API
                const response = await axios.post(`${this.apiUrl}/auth/login`, {
                    phone: this.phone,
                    password: this.password
                });
                
                if (response.data.success) {
                    // Сохраняем токен
                    localStorage.setItem('driver_token', response.data.token);
                    localStorage.setItem('driver_id', response.data.driver_id);
                    
                    this.isAuthenticated = true;
                    this.driverInfo = response.data.driver;
                    this.balance = response.data.balance || 0;
                    
                    this.showNotification('success', 'Успешно', 'Вы успешно вошли в систему');
                    
                    // Переходим на главный экран
                    this.showMainScreen();
                    
                } else {
                    this.showNotification('error', 'Ошибка', response.data.message || 'Неверные данные');
                }
                
            } catch (error) {
                console.error('Login error:', error);
                this.showNotification('error', 'Ошибка', 'Ошибка подключения к серверу');
                
                // Для тестирования - имитация успешного входа
                this.simulateLogin();
            }
        },
        
        simulateLogin() {
            // Имитация успешного входа для тестирования
            setTimeout(() => {
                this.isAuthenticated = true;
                this.driverInfo = {
                    id: 1,
                    first_name: 'Иван',
                    last_name: 'Иванов',
                    rating: 4.8
                };
                this.balance = 1500;
                this.showMainScreen();
                this.showNotification('success', 'Тестовый режим', 'Вы вошли в тестовом режиме');
            }, 1000);
        },
        
        logout() {
            localStorage.removeItem('driver_token');
            localStorage.removeItem('driver_id');
            this.isAuthenticated = false;
            
            // Останавливаем таймеры
            this.stopAllTimers();
            
            // Закрываем WebSocket
            if (this.ws) {
                this.ws.close();
            }
            
            this.showLoginScreen();
            this.showNotification('info', 'Выход', 'Вы вышли из системы');
        },
        
        // ======================
        // РЕГИСТРАЦИЯ ВОДИТЕЛЯ
        // ======================
        
        nextRegistrationStep() {
            if (this.regStep < 4) {
                this.regStep++;
            }
        },
        
        prevRegistrationStep() {
            if (this.regStep > 1) {
                this.regStep--;
            }
        },
        
        async submitRegistration() {
            if (!this.validateRegistrationData()) {
                return;
            }
            
            try {
                const response = await axios.post(`${this.apiUrl}/drivers/register`, this.regData);
                
                if (response.data.success) {
                    this.showNotification('success', 'Успешно', 'Заявка отправлена на рассмотрение');
                    this.showLoginScreen();
                } else {
                    this.showNotification('error', 'Ошибка', response.data.message);
                }
            } catch (error) {
                console.error('Registration error:', error);
                this.showNotification('error', 'Ошибка', 'Ошибка отправки заявки');
            }
        },
        
        validateRegistrationData() {
            // Простая валидация
            if (!this.regData.firstName || !this.regData.lastName) {
                this.showNotification('error', 'Ошибка', 'Заполните ФИО');
                return false;
            }
            
            if (!this.regData.carBrand || !this.regData.carModel || !this.regData.carPlate) {
                this.showNotification('error', 'Ошибка', 'Заполните данные автомобиля');
                return false;
            }
            
            if (!this.regData.licenseNumber) {
                this.showNotification('error', 'Ошибка', 'Заполните данные прав');
                return false;
            }
            
            if (!this.regData.agreeTerms) {
                this.showNotification('error', 'Ошибка', 'Необходимо согласие с условиями');
                return false;
            }
            
            return true;
        },
        
        uploadDocument(type) {
            // Имитация загрузки документа
            this.showNotification('info', 'Загрузка', 'В реальном приложении здесь загрузка файла');
            this.regData.documents[type] = 'uploaded';
        },
        
        formatDate(dateString) {
            if (!dateString) return 'Не указано';
            const date = new Date(dateString);
            return date.toLocaleDateString('ru-RU');
        },
        
        // ======================
        // РАБОТА ВОДИТЕЛЯ
        // ======================
        
        async goOnline() {
            try {
                const response = await axios.put(`${this.apiUrl}/drivers/${this.driverInfo.id}/status`, {
                    status: 'online'
                });
                
                if (response.data.success) {
                    this.driverStatus = 'online';
                    this.statusText = 'На линии';
                    this.startOnlineTimer();
                    this.showNotification('success', 'Успешно', 'Вы вышли на линию');
                    
                    // Запрашиваем разрешение на геолокацию
                    this.requestLocationPermission();
                    
                } else {
                    this.showNotification('error', 'Ошибка', response.data.message);
                }
            } catch (error) {
                console.error('Go online error:', error);
                // Имитация для тестирования
                this.driverStatus = 'online';
                this.statusText = 'На линии (тест)';
                this.startOnlineTimer();
                this.showNotification('info', 'Тест', 'Вы в тестовом режиме онлайн');
            }
        },
        
        async goOffline() {
            try {
                const response = await axios.put(`${this.apiUrl}/drivers/${this.driverInfo.id}/status`, {
                    status: 'offline'
                });
                
                if (response.data.success) {
                    this.driverStatus = 'offline';
                    this.statusText = 'Не на линии';
                    this.stopOnlineTimer();
                    this.showNotification('success', 'Успешно', 'Вы ушли с линии');
                } else {
                    this.showNotification('error', 'Ошибка', response.data.message);
                }
            } catch (error) {
                console.error('Go offline error:', error);
                // Имитация для тестирования
                this.driverStatus = 'offline';
                this.statusText = 'Не на линии';
                this.stopOnlineTimer();
                this.showNotification('info', 'Тест', 'Вы в тестовом режиме офлайн');
            }
        },
        
        startOnlineTimer() {
            this.onlineTime = 0;
            this.onlineTimer = setInterval(() => {
                this.onlineTime++;
            }, 1000);
        },
        
        stopOnlineTimer() {
            if (this.onlineTimer) {
                clearInterval(this.onlineTimer);
                this.onlineTimer = null;
            }
        },
        
        formatOnlineTime(seconds) {
            const hours = Math.floor(seconds / 3600);
            const minutes = Math.floor((seconds % 3600) / 60);
            const secs = seconds % 60;
            
            if (hours > 0) {
                return `${hours}ч ${minutes}м`;
            } else if (minutes > 0) {
                return `${minutes}м ${secs}с`;
            } else {
                return `${secs}с`;
            }
        },
        
        formatDuration(seconds) {
            const hours = Math.floor(seconds / 3600);
            const minutes = Math.floor((seconds % 3600) / 60);
            const secs = seconds % 60;
            
            if (hours > 0) {
                return `${hours}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
            } else {
                return `${minutes}:${secs.toString().padStart(2, '0')}`;
            }
        },
        
        // ======================
        // ЗАКАЗЫ
        // ======================
        
        async loadNearbyOrders() {
            if (this.driverStatus !== 'online') return;
            
            try {
                // Получаем текущую геопозицию
                const position = await this.getCurrentPosition();
                
                // Запрашиваем заказы поблизости
                const response = await axios.get(`${this.apiUrl}/orders/nearby`, {
                    params: {
                        lat: position.coords.latitude,
                        lon: position.coords.longitude,
                        radius: 5 // км
                    }
                });
                
                if (response.data.success) {
                    this.nearbyOrders = response.data.orders;
                    
                    // Обновляем маркеры на карте
                    this.updateOrderMarkers();
                }
            } catch (error) {
                console.error('Load nearby orders error:', error);
                // Имитация для тестирования
                this.simulateNearbyOrders();
            }
        },
        
        simulateNearbyOrders() {
            // Тестовые данные заказов
            this.nearbyOrders = [
                {
                    id: 1,
                    pickup_address: 'ул. Ленина, 10',
                    destination_address: 'ТЦ "Москва"',
                    distance_km: 2.5,
                    duration_minutes: 15,
                    price: 250
                },
                {
                    id: 2,
                    pickup_address: 'пр. Мира, 25',
                    destination_address: 'Ж/д вокзал',
                    distance_km: 3.8,
                    duration_minutes: 20,
                    price: 320
                }
            ];
        },
        
        viewOrderDetails(order) {
            this.showNotification('info', 'Заказ', `Откроется детальная информация о заказе #${order.id}`);
            // В реальном приложении открываем модальное окно с деталями
        },
        
        async acceptOrder() {
            if (!this.newOrder) return;
            
            try {
                const response = await axios.post(
                    `${this.apiUrl}/drivers/${this.driverInfo.id}/accept-order/${this.newOrder.id}`
                );
                
                if (response.data.success) {
                    this.currentOrder = this.newOrder;
                    this.newOrder = null;
                    this.driverStatus = 'busy';
                    this.statusText = 'Выполняю заказ';
                    this.rideStep = 1;
                    this.startRideTimer();
                    
                    this.stopOrderTimer();
                    this.showNotification('success', 'Успешно', 'Вы приняли заказ');
                    
                    // Строим маршрут к пассажиру
                    this.buildRouteToPickup();
                    
                } else {
                    this.showNotification('error', 'Ошибка', response.data.message);
                }
            } catch (error) {
                console.error('Accept order error:', error);
                // Имитация для тестирования
                this.simulateAcceptOrder();
            }
        },
        
        simulateAcceptOrder() {
            this.currentOrder = this.newOrder;
            this.newOrder = null;
            this.driverStatus = 'busy';
            this.statusText = 'Выполняю заказ (тест)';
            this.rideStep = 1;
            this.startRideTimer();
            this.stopOrderTimer();
            this.showNotification('info', 'Тест', 'Заказ принят в тестовом режиме');
        },
        
        declineOrder() {
            if (!this.newOrder) return;
            
            this.showNotification('info', 'Отклонено', `Вы отклонили заказ #${this.newOrder.id}`);
            this.newOrder = null;
            this.stopOrderTimer();
        },
        
        startOrderTimer() {
            this.orderTimer = 30;
            this.orderTimerInterval = setInterval(() => {
                this.orderTimer--;
                if (this.orderTimer <= 0) {
                    this.stopOrderTimer();
                    this.declineOrder();
                }
            }, 1000);
        },
        
        stopOrderTimer() {
            if (this.orderTimerInterval) {
                clearInterval(this.orderTimerInterval);
                this.orderTimerInterval = null;
            }
        },
        
        // ======================
        // ВЫПОЛНЕНИЕ ЗАКАЗА
        // ======================
        
        arriveAtPickup() {
            if (this.rideStep !== 1) return;
            
            this.rideStep = 2;
            this.showNotification('info', 'Прибытие', 'Вы прибыли к пассажиру');
        },
        
        startRide() {
            if (this.rideStep !== 2) return;
            
            this.rideStep = 3;
            this.showNotification('info', 'Начало', 'Поездка началась');
            
            // Строим маршрут к точке назначения
            this.buildRouteToDestination();
        },
        
        completeRide() {
            if (this.rideStep !== 3) return;
            
            this.rideStep = 4;
            this.showNotification('success', 'Завершение', 'Поездка завершена');
            
            // Имитация получения оплаты
            setTimeout(() => {
                this.finishRide();
            }, 2000);
        },
        
        finishRide() {
            // Сброс состояния
            this.currentOrder = null;
            this.driverStatus = 'online';
            this.statusText = 'На линии';
            this.rideStep = 1;
            this.stopRideTimer();
            
            // Обновляем баланс
            if (this.currentOrder) {
                this.balance += this.currentOrder.price * 0.8; // Минус комиссия 20%
            }
            
            this.showNotification('success', 'Успешно', 'Поездка завершена, средства зачислены');
        },
        
        startRideTimer() {
            this.rideTimer = 0;
            this.rideTimerInterval = setInterval(() => {
                this.rideTimer++;
            }, 1000);
        },
        
        stopRideTimer() {
            if (this.rideTimerInterval) {
                clearInterval(this.rideTimerInterval);
                this.rideTimerInterval = null;
            }
        },
        
        callPassenger() {
            if (!this.currentOrder || !this.currentOrder.passenger_phone) {
                this.showNotification('info', 'Звонок', 'Номер пассажира не указан');
                return;
            }
            
            // Имитация звонка
            this.showNotification('info', 'Звонок', `Звонок пассажиру: ${this.currentOrder.passenger_phone}`);
        },
        
        // ======================
        // ПРОБЛЕМЫ
        // ======================
        
        showProblemModal() {
            this.selectedProblem = null;
            this.problemDescription = '';
            this.showModal('problem-modal');
        },
        
        selectProblem(problem) {
            this.selectedProblem = problem;
        },
        
        submitProblem() {
            if (!this.selectedProblem) {
                this.showNotification('error', 'Ошибка', 'Выберите тип проблемы');
                return;
            }
            
            const problemData = {
                problem_type: this.selectedProblem.name,
                description: this.problemDescription,
                order_id: this.currentOrder ? this.currentOrder.id : null,
                timestamp: new Date().toISOString()
            };
            
            // Отправляем проблему на сервер
            this.sendProblemToServer(problemData);
            
            this.closeModal('problem-modal');
            this.showNotification('success', 'Спасибо', 'Проблема отправлена в поддержку');
        },
        
        async sendProblemToServer(data) {
            try {
                await axios.post(`${this.apiUrl}/problems`, data);
            } catch (error) {
                console.error('Send problem error:', error);
            }
        },
        
        // ======================
        // ГЕОЛОКАЦИЯ И КАРТА
        // ======================
        
        initMap() {
            // Инициализация Яндекс.Карт
            if (!ymaps) {
                console.error('Yandex Maps not loaded');
                return;
            }
            
            ymaps.ready(() => {
                // Центр по умолчанию (Москва)
                const defaultCenter = [55.7558, 37.6176];
                
                this.map = new ymaps.Map('map', {
                    center: defaultCenter,
                    zoom: 12,
                    controls: ['zoomControl', 'fullscreenControl']
                });
                
                // Создаем маркер для своей позиции
                this.myLocationMarker = new ymaps.Placemark(defaultCenter, {
                    balloonContent: 'Ваше местоположение'
                }, {
                    preset: 'islands#blueDotIcon'
                });
                
                this.map.geoObjects.add(this.myLocationMarker);
                
                console.log('Карта инициализирована');
            });
        },
        
        async getCurrentPosition() {
            return new Promise((resolve, reject) => {
                if (!navigator.geolocation) {
                    reject(new Error('Geolocation not supported'));
                    return;
                }
                
                navigator.geolocation.getCurrentPosition(
                    position => resolve(position),
                    error => reject(error),
                    {
                        enableHighAccuracy: true,
                        timeout: 5000,
                        maximumAge: 0
                    }
                );
            });
        },
        
        async requestLocationPermission() {
            try {
                const position = await this.getCurrentPosition();
                this.updateMyLocation(position.coords);
                return true;
            } catch (error) {
                console.error('Location permission error:', error);
                this.showNotification('warning', 'Геолокация', 'Разрешите доступ к геолокации для работы');
                return false;
            }
        },
        
        startLocationUpdates() {
            if (!navigator.geolocation) return;
            
            // Обновляем позицию каждые 10 секунд
            this.locationWatchId = navigator.geolocation.watchPosition(
                position => {
                    this.updateMyLocation(position.coords);
                    
                    // Отправляем позицию на сервер
                    this.sendLocationToServer(position.coords);
                },
                error => {
                    console.error('Location update error:', error);
                },
                {
                    enableHighAccuracy: true,
                    maximumAge: 10000,
                    timeout: 5000
                }
            );
        },
        
        stopLocationUpdates() {
            if (this.locationWatchId && navigator.geolocation) {
                navigator.geolocation.clearWatch(this.locationWatchId);
                this.locationWatchId = null;
            }
        },
        
        updateMyLocation(coords) {
            const newCoords = [coords.latitude, coords.longitude];
            
            // Обновляем позицию маркера
            if (this.myLocationMarker) {
                this.myLocationMarker.geometry.setCoordinates(newCoords);
            }
            
            // Центрируем карту
            if (this.map) {
                this.map.setCenter(newCoords, 15);
            }
        },
        
        async sendLocationToServer(coords) {
            if (!this.driverInfo.id || this.driverStatus === 'offline') return;
            
            try {
                await axios.post(`${this.apiUrl}/drivers/${this.driverInfo.id}/location`, {
                    lat: coords.latitude,
                    lon: coords.longitude,
                    speed: coords.speed || null,
                    heading: coords.heading || null
                });
            } catch (error) {
                console.error('Send location error:', error);
            }
        },
        
        centerOnLocation() {
            if (navigator.geolocation) {
                navigator.geolocation.getCurrentPosition(
                    position => {
                        const coords = [position.coords.latitude, position.coords.longitude];
                        if (this.map) {
                            this.map.setCenter(coords, 15);
                        }
                    },
                    error => {
                        console.error('Center location error:', error);
                    }
                );
            }
        },
        
        toggleTraffic() {
            if (!this.map) return;
            
            this.trafficEnabled = !this.trafficEnabled;
            
            if (this.trafficEnabled) {
                this.map.geoObjects.add(new ymaps.layer.TrafficLayer());
                this.showNotification('info', 'Пробки', 'Пробки включены');
            } else {
                this.map.geoObjects.each(layer => {
                    if (layer instanceof ymaps.layer.TrafficLayer) {
                        this.map.geoObjects.remove(layer);
                    }
                });
                this.showNotification('info', 'Пробки', 'Пробки выключены');
            }
        },
        
        updateOrderMarkers() {
            // Очищаем старые маркеры
            this.orderMarkers.forEach(marker => {
                this.map.geoObjects.remove(marker);
            });
            this.orderMarkers = [];
            
            // Добавляем новые маркеры
            this.nearbyOrders.forEach(order => {
                if (order.pickup_lat && order.pickup_lon) {
                    const marker = new ymaps.Placemark(
                        [order.pickup_lat, order.pickup_lon],
                        {
                            balloonContent: `
                                <b>Заказ #${order.id}</b><br>
                                Откуда: ${order.pickup_address}<br>
                                Куда: ${order.destination_address}<br>
                                Цена: ${order.price}₽
                            `
                        },
                        {
                            preset: 'islands#redDotIcon'
                        }
                    );
                    
                    this.map.geoObjects.add(marker);
                    this.orderMarkers.push(marker);
                }
            });
        },
        
        buildRouteToPickup() {
            if (!this.map || !this.currentOrder || !this.currentOrder.pickup_lat) return;
            
            // В реальном приложении здесь построение маршрута через Яндекс.Маршрутизацию
            this.showNotification('info', 'Маршрут', 'Строится маршрут к пассажиру...');
        },
        
        buildRouteToDestination() {
            if (!this.map || !this.currentOrder || !this.currentOrder.destination_lat) return;
            
            // В реальном приложении здесь построение маршрута через Яндекс.Маршрутизацию
            this.showNotification('info', 'Маршрут', 'Строится маршрут к точке назначения...');
        },
        
        // ======================
        // WebSocket
        // ======================
        
        connectWebSocket() {
            if (!this.driverInfo.id || this.wsConnected) return;
            
            const driverId = this.driverInfo.id;
            this.ws = new WebSocket(`${this.wsUrl}/driver/${driverId}`);
            
            this.ws.onopen = () => {
                console.log('WebSocket connected');
                this.wsConnected = true;
                this.sendWebSocketMessage({
                    type: 'driver_online',
                    driver_id: driverId,
                    status: this.driverStatus
                });
            };
            
            this.ws.onmessage = (event) => {
                const message = JSON.parse(event.data);
                this.handleWebSocketMessage(message);
            };
            
            this.ws.onclose = () => {
                console.log('WebSocket disconnected');
                this.wsConnected = false;
                
                // Пытаемся переподключиться через 5 секунд
                setTimeout(() => {
                    if (this.isAuthenticated) {
                        this.connectWebSocket();
                    }
                }, 5000);
            };
            
            this.ws.onerror = (error) => {
                console.error('WebSocket error:', error);
            };
        },
        
        sendWebSocketMessage(message) {
            if (this.ws && this.ws.readyState === WebSocket.OPEN) {
                this.ws.send(JSON.stringify(message));
            }
        },
        
        handleWebSocketMessage(message) {
            switch (message.type) {
                case 'new_order':
                    this.handleNewOrder(message.order);
                    break;
                    
                case 'order_update':
                    this.handleOrderUpdate(message);
                    break;
                    
                case 'driver_status_update':
                    this.handleDriverStatusUpdate(message);
                    break;
                    
                case 'message':
                    this.handleChatMessage(message);
                    break;
                    
                case 'ping':
                    this.sendWebSocketMessage({ type: 'pong' });
                    break;
            }
        },
        
        handleNewOrder(order) {
            if (this.driverStatus !== 'online' || this.currentOrder) return;
            
            this.newOrder = order;
            this.startOrderTimer();
            
            // Показываем уведомление
            this.showNotification('warning', 'Новый заказ!', 'У вас есть 30 секунд чтобы принять заказ');
            
            // Проигрываем звук (если разрешено)
            this.playNotificationSound();
        },
        
        handleOrderUpdate(message) {
            if (!this.currentOrder || this.currentOrder.id !== message.order_id) return;
            
            // Обновляем статус заказа
            this.currentOrder.status = message.status;
            
            switch (message.status) {
                case 'cancelled':
                    this.showNotification('info', 'Отмена', 'Пассажир отменил заказ');
                    this.finishRide();
                    break;
                    
                case 'completed':
                    this.showNotification('success', 'Завершено', 'Пассажир подтвердил завершение поездки');
                    break;
            }
        },
        
        // ======================
        // УТИЛИТЫ
        // ======================
        
        formatBalance(amount) {
            return new Intl.NumberFormat('ru-RU').format(amount);
        },
        
        shortenAddress(address, maxLength = 30) {
            if (!address) return '';
            if (address.length <= maxLength) return address;
            return address.substring(0, maxLength) + '...';
        },
        
        calculateDistanceToOrder(order) {
            // В реальном приложении здесь расчет расстояния
            return Math.floor(Math.random() * 500) + 100; // Тестовые данные
        },
        
        setActiveTab(tab) {
            this.activeTab = tab;
            
            switch (tab) {
                case 'home':
                    // Загружаем данные для главной
                    break;
                    
                case 'orders':
                    // Показываем историю заказов
                    this.showNotification('info', 'Заказы', 'История заказов будет здесь');
                    break;
                    
                case 'balance':
                    // Показываем баланс и операции
                    this.showNotification('info', 'Баланс', 'История операций будет здесь');
                    break;
                    
                case 'stats':
                    // Показываем статистику
                    this.showNotification('info', 'Статистика', 'Статистика будет здесь');
                    break;
                    
                case 'settings':
                    // Показываем настройки
                    this.showNotification('info', 'Настройки', 'Настройки будут здесь');
                    break;
            }
        },
        
        async loadDriverData() {
            // Загружаем данные водителя
            try {
                // Загрузка профиля
                const profileResponse = await axios.get(`${this.apiUrl}/drivers/${this.driverInfo.id}/profile`);
                this.driverInfo = { ...this.driverInfo, ...profileResponse.data };
                
                // Загрузка статистики
                const statsResponse = await axios.get(`${this.apiUrl}/drivers/${this.driverInfo.id}/stats`);
                this.driverStats = statsResponse.data;
                
                // Загрузка сегодняшней статистики
                const todayResponse = await axios.get(`${this.apiUrl}/drivers/${this.driverInfo.id}/stats/today`);
                this.todayStats = todayResponse.data;
                
            } catch (error) {
                console.error('Load driver data error:', error);
            }
        },
        
        showNotification(type, title, message) {
            const container = document.getElementById('notification-container');
            
            const notification = document.createElement('div');
            notification.className = `notification ${type}`;
            notification.innerHTML = `
                <div class="notification-icon">
                    <i class="fas fa-${this.getNotificationIcon(type)}"></i>
                </div>
                <div class="notification-content">
                    <div class="notification-title">${title}</div>
                    <div class="notification-message">${message}</div>
                </div>
            `;
            
            container.appendChild(notification);
            
            // Автоматическое удаление через 5 секунд
            setTimeout(() => {
                notification.remove();
            }, 5000);
        },
        
        getNotificationIcon(type) {
            switch (type) {
                case 'success': return 'check-circle';
                case 'error': return 'exclamation-circle';
                case 'warning': return 'exclamation-triangle';
                case 'info': return 'info-circle';
                default: return 'bell';
            }
        },
        
        showModal(modalId) {
            const modal = document.getElementById(modalId);
            if (modal) {
                modal.style.display = 'flex';
            }
        },
        
        closeModal(modalId) {
            const modal = document.getElementById(modalId);
            if (modal) {
                modal.style.display = 'none';
            }
        },
        
        playNotificationSound() {
            // В реальном приложении здесь воспроизведение звука
            console.log('Notification sound played');
        },
        
        stopAllTimers() {
            this.stopOnlineTimer();
            this.stopOrderTimer();
            this.stopRideTimer();
            this.stopLocationUpdates();
        },
        
        // ======================
        // СЛУЖЕБНЫЕ МЕТОДЫ
        // ======================
        
        showForgotPassword() {
            this.showNotification('info', 'Восстановление', 'Функция восстановления пароля в разработке');
        },
        
        editProfile() {
            this.showNotification('info', 'Редактирование', 'Редактирование профиля в разработке');
        },
        
        changePassword() {
            this.showNotification('info', 'Пароль', 'Смена пароля в разработке');
        },
        
        showCarInfo() {
            this.showNotification('info', 'Автомобиль', 'Информация об автомобиле в разработке');
        },
        
        showDocuments() {
            this.showNotification('info', 'Документы', 'Просмотр документов в разработке');
        },
        
        showSecuritySettings() {
            this.showNotification('info', 'Безопасность', 'Настройки безопасности в разработке');
        },
        
        showTerms() {
            this.showNotification('info', 'Условия', 'Условия использования в разработке');
        },
        
        showPrivacy() {
            this.showNotification('info', 'Конфиденциальность', 'Политика конфиденциальности в разработке');
        },
        
        showNotifications() {
            this.showNotification('info', 'Уведомления', 'Список уведомлений в разработке');
        }
    },
    
    beforeDestroy() {
        // Очистка ресурсов при уничтожении компонента
        this.stopAllTimers();
        
        if (this.ws) {
            this.ws.close();
        }
    }
});

// Глобальные вспомогательные функции
function showTestNotification() {
    app.showNotification('success', 'Тест', 'Это тестовое уведомление!');
}

// Экспорт для отладки
window.app = app;