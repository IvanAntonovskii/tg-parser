import requests
import logging
import asyncio
import aiohttp
import random
import json
import os
import io
import re
import math
from datetime import datetime
from bs4 import BeautifulSoup
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance
from config import Config

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class CryptoNewsBot:
    def __init__(self):
        self.token = Config.TELEGRAM_BOT_TOKEN
        self.channel = Config.CHANNEL_ID
        self.session = None
        self.published_news = set()
        self.published_signals = set()
        self.load_published_news()

        # Фразы для постов
        self.viral_phrases = [
            "ЗАЛЕТАЕМ В ТРЕНДЫ!",
            "ХАЙП НА СТАРТЕ!",
            "ГОРИМ, НО НЕ СДАЕМСЯ!",
            "ВЗЛЕТАЕМ НА ЛУНУ!",
            "БОМБИЧЕСКИЕ НОВОСТИ!",
            "ВНИМАНИЕ, ХАЙП!",
            "ТОЧКА ВХОДА!",
            "МОМЕНТ ИСТИНЫ!",
            "ЗВЕЗДНЫЙ ЧАС!",
            "БОМБА ДНЯ!"
        ]

        self.signal_phrases = [
            "🚀 СИГНАЛ НА ПОКУПКУ!",
            "💎 ВИЖУ РОСТ!",
            "📈 ЛОВИМ ВОЛНУ!",
            "🔥 ГОРИМ НА ПРОФИТЕ!",
            "🎯 ТОЧКА ВХОДА ОТМЕЧЕНА!",
            "⚡ МОМЕНТ ИСТИНЫ!",
            "💸 ЗАРАБАТЫВАЕМ ВМЕСТЕ!",
            "🌟 ЗВЕЗДНЫЙ СИГНАЛ!"
        ]

        self.emojis = ["🚀", "💎", "🔥", "📈", "💥", "🎯", "⚡", "🌟", "💣", "🎊", "👑", "💸", "🤑", "👀"]

        logger.info("ANT CAPITAL Bot инициализирован")

    def ai_translate_text(self, text: str) -> str:
        """Умный перевод и адаптация текста для русскоязычной аудитории"""
        try:
            if not text:
                return "Анализ рынка и перспективные возможности"

            # Если текст уже на русском, просто очищаем его
            if any(char in 'абвгдеёжзийклмнопрстуфхцчшщъыьэюя' for char in text.lower()):
                return self.clean_text(text)

            # Упрощенный и более эффективный перевод
            translation_map = {
                # Крипто термины
                'bitcoin': 'Биткоин', 'btc': 'BTC', 'bitcoins': 'Биткоины',
                'ethereum': 'Ethereum', 'eth': 'ETH',
                'crypto': 'крипто', 'cryptocurrency': 'криптовалюта',
                'blockchain': 'блокчейн', 'defi': 'DeFi', 'nft': 'NFT',
                'token': 'токен', 'coin': 'монета', 'altcoin': 'альткоин',
                'exchange': 'биржа', 'wallet': 'кошелек',
                'mining': 'майнинг', 'staking': 'стейкинг',

                # Трейдинг термины
                'price': 'цена', 'prices': 'цены',
                'market': 'рынок', 'markets': 'рынки',
                'trading': 'трейдинг', 'trade': 'сделка',
                'signal': 'сигнал', 'signals': 'сигналы',
                'bullish': 'бычий', 'bearish': 'медвежий',
                'rally': 'ралли', 'crash': 'обвал',
                'volatility': 'волатильность', 'liquidity': 'ликвидность',
                'volume': 'объем', 'resistance': 'сопротивление',
                'support': 'поддержка', 'breakout': 'пробитие',
                'breakdown': 'слом уровня',

                # Общие финансовые термины
                'investment': 'инвестиция', 'investor': 'инвестор',
                'analysis': 'анализ', 'analyst': 'аналитик',
                'prediction': 'прогноз', 'forecast': 'прогноз',
                'growth': 'рост', 'decline': 'снижение',
                'performance': 'динамика', 'activity': 'активность',

                # Прилагательные
                'strong': 'сильный', 'weak': 'слабый',
                'high': 'высокий', 'low': 'низкий',
                'rapid': 'быстрый', 'slow': 'медленный',
                'major': 'крупный', 'minor': 'незначительный',
                'significant': 'значительный', 'important': 'важный',
                'explosive': 'взрывной', 'rare': 'редкий',

                # Глаголы и наречия
                'could': 'может', 'should': 'должен',
                'might': 'возможно', 'will': 'будет',
                'forming': 'формируется', 'catching': 'застает',
                'off-guard': 'врасплох', 'bottom': 'дно',
                'top': 'вершина', 'momentum': 'импульс',
                'underperformance': 'неудовлетворительная динамика',
                'contrasts': 'контрастирует с', 'real': 'реальная',
                'see': 'узнайте', 'how': 'как',
            }

            # Приводим текст к нижнему регистру для сравнения
            lower_text = text.lower()

            # Сначала проверяем фразовые замены
            phrase_replacements = [
                (r'bitcoin price prediction', 'Прогноз цены Биткоина'),
                (r'ethereum price prediction', 'Прогноз цены Ethereum'),
                (r'rare bitcoin futures signal', 'Редкий сигнал по фьючерсам Биткоина'),
                (r'is bottom forming', 'формируется ли дно'),
                (r'could catch traders off-guard', 'может застать трейдеров врасплох'),
                (r'market analysis', 'анализ рынка'),
                (r'trading opportunity', 'торговая возможность'),
                (r'breaking news', 'экстренные новости'),
                (r'latest update', 'последнее обновление'),
                (r'underperformance contrasts with explosive growth',
                 'неудовлетворительная динамика контрастирует со взрывным ростом'),
                (r'cointelegraph rare', 'Cointelegraph: редкий'),
                (r'futures signal', 'сигнал по фьючерсам'),
            ]

            translated_text = text
            for eng_phrase, rus_phrase in phrase_replacements:
                if re.search(eng_phrase, lower_text, re.IGNORECASE):
                    translated_text = re.sub(eng_phrase, rus_phrase, translated_text, flags=re.IGNORECASE)
                    break

            # Если фразовая замена не сработала, используем пословный перевод
            if translated_text == text:
                words = text.split()
                translated_words = []

                for word in words:
                    clean_word = re.sub(r'[^\w]', '', word.lower())
                    if clean_word in translation_map:
                        # Сохраняем оригинальный регистр первого символа
                        if word[0].isupper():
                            translated_word = translation_map[clean_word].capitalize()
                        else:
                            translated_word = translation_map[clean_word]
                        translated_words.append(translated_word)
                    else:
                        translated_words.append(word)

                translated_text = ' '.join(translated_words)

            # Очищаем и форматируем финальный текст
            final_text = self.clean_text(translated_text)

            # Убедимся, что первая буква заглавная
            if final_text and final_text[0].isalpha():
                final_text = final_text[0].upper() + final_text[1:]

            logger.info(f"Перевод: '{text[:50]}...' -> '{final_text[:50]}...'")
            return final_text

        except Exception as e:
            logger.error(f"Ошибка перевода: {e}")
            return self.clean_text(text)

    def clean_text(self, text: str) -> str:
        """Очищает и форматирует текст"""
        if not text:
            return "Актуальные рыночные инсайты и аналитика"

        # Удаляем лишние символы, но сохраняем основные пунктуацию
        text = re.sub(r'[^\w\s\.\,\!\?\-\+\$\%\(\)\:\;]', '', text)

        # Заменяем множественные пробелы на один
        text = re.sub(r'\s+', ' ', text)

        # Удаляем пробелы перед знаками препинания
        text = re.sub(r'\s+([\.\,\!\?])', r'\1', text)

        # Удаляем начальные и конечные пробелы
        text = text.strip()

        return text

    def analyze_content(self, text: str) -> dict:
        """Анализирует содержание текста для определения темы изображения"""
        text_lower = text.lower()

        # Определяем основные категории контента
        categories = {
            'bitcoin': any(word in text_lower for word in ['bitcoin', 'btc', 'биткоин']),
            'ethereum': any(word in text_lower for word in ['ethereum', 'eth', 'эфириум']),
            'trading': any(
                word in text_lower for word in ['трейдинг', 'трейдер', 'trading', 'trader', 'сигнал', 'анализ']),
            'price': any(word in text_lower for word in ['цена', 'price', 'стоимость', 'cost']),
            'growth': any(word in text_lower for word in ['рост', 'growth', 'увеличени', 'повышен']),
            'crash': any(word in text_lower for word in ['падени', 'crash', 'снижен', 'drop']),
            'politics': any(
                word in text_lower for word in ['трамп', 'trump', 'байден', 'biden', 'политик', 'government']),
            'regulation': any(word in text_lower for word in ['регулирован', 'regulation', 'закон', 'law']),
            'technology': any(word in text_lower for word in ['технолог', 'technology', 'разработк', 'development']),
            'institution': any(
                word in text_lower for word in ['институц', 'institution', 'банк', 'bank', 'фонд', 'fund']),
        }

        # Определяем основной тип контента
        content_type = 'general'
        if categories['trading']:
            content_type = 'trading'
        elif categories['bitcoin']:
            content_type = 'bitcoin'
        elif categories['ethereum']:
            content_type = 'ethereum'
        elif categories['politics']:
            content_type = 'politics'
        elif categories['regulation']:
            content_type = 'regulation'

        return {
            'categories': categories,
            'content_type': content_type,
            'is_positive': categories['growth'] and not categories['crash'],
            'is_technical': categories['trading'] or categories['price']
        }

    def create_trading_chart_image(self, theme: str, analysis: dict) -> Image.Image:
        """Создает изображение с графиком для торговых сигналов"""
        width, height = 1200, 900
        image = Image.new('RGB', (width, height), color=(25, 30, 45))
        draw = ImageDraw.Draw(image)

        # Цвета в зависимости от настроения
        if analysis['is_positive']:
            line_color = (76, 175, 80)  # зеленый
            bg_color = (30, 40, 35)
        else:
            line_color = (244, 67, 54)  # красный
            bg_color = (40, 30, 35)

        # Рисуем сетку графика
        for i in range(0, width, 50):
            draw.line([(i, 0), (i, height)], fill=(50, 50, 60), width=1)
        for i in range(0, height, 50):
            draw.line([(0, i), (width, i)], fill=(50, 50, 60), width=1)

        # Создаем реалистичный график цены
        points = []
        x = 0
        y = height // 2
        volatility = random.randint(20, 80)
        trend = 1 if analysis['is_positive'] else -1

        for i in range(width // 10):
            x = i * 10
            # Добавляем тренд + случайные колебания
            y_change = trend * random.randint(5, 15) + random.randint(-volatility, volatility)
            y = max(50, min(height - 50, y + y_change))
            points.append((x, y))

        # Рисуем линию графика
        if len(points) > 1:
            draw.line(points, fill=line_color, width=4)

        # Добавляем свечи (японские свечи)
        for i in range(10, width - 50, 80):
            candle_x = i
            candle_high = random.randint(100, height - 100)
            candle_low = candle_high + random.randint(30, 100)
            candle_open = random.randint(candle_high, candle_low)
            candle_close = random.randint(candle_high, candle_low)

            # Тело свечи
            body_color = line_color if candle_close > candle_open else (244, 67, 54)
            draw.rectangle([candle_x - 15, min(candle_open, candle_close),
                            candle_x + 15, max(candle_open, candle_close)],
                           fill=body_color)

            # Тени свечи
            draw.line([(candle_x, candle_high), (candle_x, min(candle_open, candle_close))],
                      fill=body_color, width=2)
            draw.line([(candle_x, max(candle_open, candle_close)), (candle_x, candle_low)],
                      fill=body_color, width=2)

        # Добавляем технические элементы
        try:
            font = ImageFont.truetype("arial.ttf", 20)
        except:
            font = ImageFont.load_default()

        # Подписи осей
        draw.text((50, 30), "Цена", fill=(200, 200, 200), font=font)
        draw.text((width - 100, height - 50), "Время", fill=(200, 200, 200), font=font)

        return image

    def create_crypto_theme_image(self, theme: str, analysis: dict) -> Image.Image:
        """Создает тематическое изображение для крипто-новостей"""
        width, height = 1200, 900
        image = Image.new('RGB', (width, height), color=(15, 20, 30))
        draw = ImageDraw.Draw(image)

        # Определяем основной символ
        if analysis['categories']['bitcoin']:
            primary_color = (255, 153, 0)  # оранжевый Bitcoin
            symbol = "₿"
        elif analysis['categories']['ethereum']:
            primary_color = (138, 43, 226)  # фиолетовый Ethereum
            symbol = "Ξ"
        else:
            primary_color = (100, 200, 255)  # синий общий
            symbol = "₿"

        # Создаем абстрактную композицию с символом
        try:
            # Большой центральный символ
            font_large = ImageFont.truetype("arial.ttf", 120)
            bbox = draw.textbbox((0, 0), symbol, font=font_large)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]

            x = (width - text_width) // 2
            y = (height - text_height) // 2

            # Рисуем символ с градиентом
            for i in range(5):
                offset = i * 2
                color = tuple(max(0, c - i * 20) for c in primary_color)
                draw.text((x + offset, y + offset), symbol, fill=color, font=font_large)
        except:
            pass

        # Добавляем цифровые элементы вокруг
        for i in range(50):
            x = random.randint(0, width)
            y = random.randint(0, height)
            size = random.randint(5, 15)
            binary = random.choice(['0', '1'])

            color = (random.randint(100, 200), random.randint(100, 200), random.randint(100, 200))
            try:
                font_small = ImageFont.truetype("arial.ttf", size)
                draw.text((x, y), binary, fill=color, font=font_small)
            except:
                pass

        # Добавляем блокчейн-цепочку
        for i in range(10):
            x = random.randint(100, width - 100)
            y = random.randint(100, height - 100)
            size = random.randint(20, 40)

            # Блок блокчейна
            draw.rectangle([x, y, x + size, y + size],
                           outline=primary_color, width=2)

            # Соединительная линия
            if i > 0:
                prev_x = x - random.randint(50, 100)
                prev_y = y
                draw.line([(prev_x, prev_y), (x, y)],
                          fill=primary_color, width=2)

        return image

    def create_political_image(self, theme: str, analysis: dict) -> Image.Image:
        """Создает изображение для политических новостей"""
        width, height = 1200, 900
        image = Image.new('RGB', (width, height), color=(35, 40, 50))
        draw = ImageDraw.Draw(image)

        # Определяем политический контекст
        if 'трамп' in theme.lower() or 'trump' in theme.lower():
            primary_color = (255, 0, 0)  # красный республиканцы
            politician = "TRUMP"
        elif 'байден' in theme.lower() or 'biden' in theme.lower():
            primary_color = (0, 100, 200)  # синий демократы
            politician = "BIDEN"
        else:
            primary_color = (150, 150, 150)  # нейтральный
            politician = "GOV"

        # Создаем абстрактное политическое изображение
        # Флаг США стилизованный
        stripes = 7
        stripe_height = height // stripes

        for i in range(stripes):
            y = i * stripe_height
            if i % 2 == 0:
                color = (200, 0, 0)  # красные полосы
            else:
                color = (255, 255, 255)  # белые полосы
            draw.rectangle([0, y, width, y + stripe_height], fill=color)

        # Синий квадрат
        draw.rectangle([0, 0, width // 3, stripe_height * 4], fill=(0, 0, 150))

        # Добавляем текст с именем политика
        try:
            font = ImageFont.truetype("arial.ttf", 60)
            bbox = draw.textbbox((0, 0), politician, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]

            x = width - text_width - 50
            y = height - text_height - 50

            draw.text((x, y), politician, fill=primary_color, font=font)
        except:
            pass

        # Добавляем элементы капитала
        # Белый дом стилизованный
        house_width = 200
        house_height = 150
        house_x = width // 2 - house_width // 2
        house_y = height // 2 - house_height // 2

        # Основание
        draw.rectangle([house_x, house_y + house_height // 2,
                        house_x + house_width, house_y + house_height],
                       fill=(255, 255, 255))

        # Крыша
        draw.polygon([(house_x, house_y + house_height // 2),
                      (house_x + house_width, house_y + house_height // 2),
                      (house_x + house_width // 2, house_y)],
                     fill=(200, 200, 200))

        return image

    def create_news_image(self, theme: str, analysis: dict) -> Image.Image:
        """Создает изображение для общих новостей"""
        width, height = 1200, 900
        image = Image.new('RGB', (width, height), color=(20, 25, 35))
        draw = ImageDraw.Draw(image)

        # Градиентный фон
        for y in range(height):
            # Плавный градиент от темного к светлому
            r = int(20 + (y / height) * 30)
            g = int(25 + (y / height) * 30)
            b = int(35 + (y / height) * 30)
            draw.line([(0, y), (width, y)], fill=(r, g, b))

        # Газетный стиль
        try:
            font_large = ImageFont.truetype("arial.ttf", 48)
            font_medium = ImageFont.truetype("arial.ttf", 24)
            font_small = ImageFont.truetype("arial.ttf", 18)
        except:
            font_large = font_medium = font_small = ImageFont.load_default()

        # Заголовок
        title = "НОВОСТИ КРИПТО"
        bbox = draw.textbbox((0, 0), title, font=font_large)
        text_width = bbox[2] - bbox[0]
        x = (width - text_width) // 2
        draw.text((x, 100), title, fill=(255, 215, 0), font=font_large)

        # Текст новости (упрощенный)
        news_text = theme[:100] + "..." if len(theme) > 100 else theme
        words = news_text.split()
        lines = []
        current_line = ""

        for word in words:
            test_line = current_line + " " + word if current_line else word
            bbox = draw.textbbox((0, 0), test_line, font=font_medium)
            if bbox[2] < width - 200:
                current_line = test_line
            else:
                lines.append(current_line)
                current_line = word

        if current_line:
            lines.append(current_line)

        # Рисуем строки текста
        y_pos = 200
        for line in lines[:6]:  # Максимум 6 строк
            bbox = draw.textbbox((0, 0), line, font=font_medium)
            text_width = bbox[2] - bbox[0]
            x = (width - text_width) // 2
            draw.text((x, y_pos), line, fill=(255, 255, 255), font=font_medium)
            y_pos += 40

        # Добавляем дату
        date_str = datetime.now().strftime("%d.%m.%Y")
        draw.text((width - 150, height - 50), date_str, fill=(150, 150, 150), font=font_small)

        return image

    def create_relevant_image(self, text: str, content_type: str) -> io.BytesIO:
        """Создает релевантное изображение на основе содержания текста"""
        try:
            # Анализируем содержание
            analysis = self.analyze_content(text)

            # Выбираем подходящий тип изображения
            if content_type == "signal" or analysis['is_technical']:
                image = self.create_trading_chart_image(text, analysis)
                style_name = "Торговый график"
            elif analysis['content_type'] == 'politics':
                image = self.create_political_image(text, analysis)
                style_name = "Политический контекст"
            elif analysis['content_type'] in ['bitcoin', 'ethereum']:
                image = self.create_crypto_theme_image(text, analysis)
                style_name = "Крипто тема"
            else:
                image = self.create_news_image(text, analysis)
                style_name = "Новостной стиль"

            # Добавляем подпись
            draw = ImageDraw.Draw(image)
            try:
                font = ImageFont.truetype("arial.ttf", 16)
            except:
                font = ImageFont.load_default()

            signature = f"ANT CAPITAL • {style_name}"
            bbox = draw.textbbox((0, 0), signature, font=font)
            text_width = bbox[2] - bbox[0]
            draw.text((image.width - text_width - 20, image.height - 30),
                      signature, fill=(150, 150, 150), font=font)

            # Конвертируем в bytes
            img_buffer = io.BytesIO()
            image.save(img_buffer, format='JPEG', quality=95, optimize=True)
            img_buffer.seek(0)

            logger.info(f"Создано релевантное изображение: {style_name}")
            return img_buffer

        except Exception as e:
            logger.error(f"Ошибка создания релевантного изображения: {e}")
            # Резервное изображение
            image = self.create_news_image(text, {'content_type': 'general'})
            img_buffer = io.BytesIO()
            image.save(img_buffer, format='JPEG')
            img_buffer.seek(0)
            return img_buffer

    def load_published_news(self):
        """Загружает историю опубликованных новостей и сигналов"""
        try:
            if os.path.exists('published_news.json'):
                with open('published_news.json', 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.published_news = set(data.get('published_news', []))
                    self.published_signals = set(data.get('published_signals', []))
                    logger.info(
                        f"Загружено {len(self.published_news)} новостей и {len(self.published_signals)} сигналов")
        except Exception as e:
            logger.error(f"Error loading published data: {e}")

    def save_published_news(self):
        """Сохраняет историю опубликованных новостей и сигналов"""
        try:
            with open('published_news.json', 'w', encoding='utf-8') as f:
                json.dump({
                    'published_news': list(self.published_news),
                    'published_signals': list(self.published_signals)
                }, f, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Error saving published data: {e}")

    async def init_session(self):
        """Инициализация HTTP сессии"""
        timeout = aiohttp.ClientTimeout(total=30)
        self.session = aiohttp.ClientSession(timeout=timeout)
        logger.info("HTTP сессия инициализирована")

    async def close_session(self):
        """Закрытие HTTP сессии"""
        if self.session:
            await self.session.close()
            logger.info("HTTP сессия закрыта")

    async def get_tradingview_signals(self):
        """Парсинг торговых сигналов с TradingView"""
        try:
            urls = [
                "https://ru.tradingview.com/ideas/",
                "https://www.tradingview.com/ideas/",
            ]

            signals = []

            for url in urls:
                try:
                    headers = {
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                    }

                    logger.info(f"Парсим сигналы с {url}")
                    async with self.session.get(url, headers=headers) as response:
                        if response.status == 200:
                            html = await response.text()
                            soup = BeautifulSoup(html, 'html.parser')

                            # Ищем заголовки с идеями
                            headlines = soup.find_all(['h3', 'h4', 'h5'])[:15]

                            for headline in headlines:
                                try:
                                    title_elem = headline.find('a')
                                    if not title_elem:
                                        continue

                                    title = title_elem.text.strip()
                                    if not title or len(title) < 10:
                                        continue

                                    # Переводим и очищаем заголовок
                                    translated_title = self.ai_translate_text(title)

                                    # Фильтруем сигналы
                                    title_upper = translated_title.upper()
                                    if not any(word in title_upper for word in
                                               ['BUY', 'LONG', 'КУПИТЬ', 'ПОКУПКА', 'РОСТ', 'BULL']):
                                        continue

                                    link = title_elem.get('href', '')
                                    if link and not link.startswith('http'):
                                        link = 'https://www.tradingview.com' + link

                                    # Извлекаем тикер
                                    ticker_match = re.search(r'([A-Z]+:[A-Z]+|[A-Z]+/USD|[A-Z]+/USDT|[A-Z]+)',
                                                             translated_title)
                                    ticker = ticker_match.group(1) if ticker_match else "CRYPTO"

                                    # Определяем тип актива
                                    asset_type = "Крипто"
                                    if any(word in ticker.upper() for word in [':US', ':NASDAQ', ':NYSE']):
                                        asset_type = "Акции"
                                    elif any(
                                            word in ticker.upper() for word in ['XAU', 'XAG', 'OIL', 'GOLD', 'SILVER']):
                                        asset_type = "Товары"
                                    elif any(word in ticker.upper() for word in ['EUR', 'USD', 'JPY', 'GBP']):
                                        asset_type = "Форекс"

                                    signal_id = hash(translated_title + ticker + url)
                                    if signal_id not in self.published_signals:
                                        signals.append({
                                            'ticker': ticker,
                                            'title': translated_title,
                                            'link': link,
                                            'asset_type': asset_type,
                                            'source': 'TradingView',
                                            'id': signal_id
                                        })

                                except Exception:
                                    continue

                except Exception as e:
                    logger.error(f"Ошибка парсинга {url}: {e}")
                    continue

            logger.info(f"Найдено {len(signals)} новых сигналов")
            return signals[:8]

        except Exception as e:
            logger.error(f"Error parsing TradingView signals: {e}")
            return []

    async def get_crypto_news_signals(self):
        """Парсинг сигналов с крипто-новостных сайтов"""
        try:
            signals = []

            # CoinGecko новости
            try:
                url = "https://www.coingecko.com/en/news"
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                }

                async with self.session.get(url, headers=headers) as response:
                    if response.status == 200:
                        html = await response.text()
                        soup = BeautifulSoup(html, 'html.parser')

                        news_items = soup.find_all('a', href=re.compile(r'/news/'))[:10]

                        for item in news_items:
                            title = item.get_text(strip=True)
                            if title and len(title) > 20:
                                translated_title = self.ai_translate_text(title)

                                coin_matches = re.findall(r'\b(BTC|ETH|BNB|ADA|DOT|SOL|XRP|DOGE|MATIC)\b',
                                                          translated_title.upper())
                                if coin_matches:
                                    ticker = coin_matches[0]
                                    link = item.get('href', '')
                                    if link and not link.startswith('http'):
                                        link = 'https://www.coingecko.com' + link

                                    signal_id = hash(translated_title + ticker + "coingecko")
                                    if signal_id not in self.published_signals:
                                        signals.append({
                                            'ticker': ticker,
                                            'title': translated_title,
                                            'link': link,
                                            'asset_type': 'Крипто',
                                            'source': 'CoinGecko',
                                            'id': signal_id
                                        })
            except Exception as e:
                logger.error(f"Ошибка парсинга CoinGecko: {e}")

            return signals[:5]

        except Exception as e:
            logger.error(f"Error parsing crypto news signals: {e}")
            return []

    async def get_generated_signals(self):
        """Генерирует сигналы если не найдены реальные"""
        try:
            crypto_pairs = [
                "BTC/USDT", "ETH/USDT", "BNB/USDT", "ADA/USDT", "XRP/USDT",
                "DOT/USDT", "LTC/USDT", "LINK/USDT", "BCH/USDT", "EOS/USDT"
            ]

            signal_types = [
                "Сильный восходящий тренд на дневном таймфрейме",
                "Пробитие ключевого уровня сопротивления",
                "Отскок от важной ценовой поддержки",
                "Бычье расхождение индикатора RSI",
                "Формирование разворотной графической модели",
                "Ускорение роста на повышенных объемах торгов"
            ]

            signals = []

            for i in range(5):
                ticker = random.choice(crypto_pairs)
                signal_type = random.choice(signal_types)

                title = f"{ticker} - {signal_type}"
                signal_id = hash(title + str(datetime.now()) + str(i))

                if signal_id not in self.published_signals:
                    signals.append({
                        'ticker': ticker,
                        'title': title,
                        'link': '',
                        'asset_type': 'Крипто',
                        'source': 'ANT CAPITAL',
                        'id': signal_id
                    })

            logger.info(f"Сгенерировано {len(signals)} сигналов")
            return signals

        except Exception as e:
            logger.error(f"Error generating signals: {e}")
            return []

    def format_signal_text(self, signal):
        """Форматирование текста для сигнала"""
        ticker = signal['ticker']
        title = self.ai_translate_text(signal['title'])
        asset_type = signal['asset_type']
        source = signal.get('source', 'Профессиональный анализ')
        link = signal.get('link', '')

        signal_phrase = random.choice(self.signal_phrases)

        text = f"<b>{signal_phrase}</b>\n\n"
        text += f"🎯 Актив: {ticker}\n"
        text += f"📊 Тип: {asset_type}\n"
        text += f"📰 Источник: {source}\n\n"

        text += f"<b>Анализ:</b>\n{title}\n\n"

        # Профессиональные рекомендации
        recommendations = [
            "📈 Рассмотреть лонг позицию",
            "💎 Установить стоп-лосс 2-3%",
            "🎯 Тейк-профит на 5-8%",
            "⏰ Таймфрейм: 4H-1D",
            "⚠️ Риск-менеджмент обязателен",
            "📊 Мониторить ключевые уровни",
            "💡 Учитывать объемы торгов"
        ]

        text += "<b>Рекомендации:</b>\n"
        for rec in random.sample(recommendations, 3):
            text += f"• {rec}\n"

        text += "\n"

        if link:
            text += f"<a href='{link}'>Подробный анализ</a>\n\n"

        text += "<b>Внимание:</b> Это не инвестиционная рекомендация. Торгуйте ответственно!\n\n"

        # Хештеги
        text += f"#{asset_type.replace(' ', '')} #{ticker.replace(':', '').replace('/', '')} #Сигнал"

        return text

    async def publish_signal(self):
        """Публикация торгового сигнала с релевантными изображениями"""
        try:
            logger.info("Проверяем новые сигналы...")

            signals_tasks = [
                self.get_tradingview_signals(),
                self.get_crypto_news_signals(),
                self.get_generated_signals()
            ]

            results = await asyncio.gather(*signals_tasks, return_exceptions=True)

            all_signals = []
            for result in results:
                if isinstance(result, list):
                    all_signals.extend(result)

            if not all_signals:
                logger.info("Новых сигналов не найдено")
                return False

            signal = random.choice(all_signals)

            # Создаем релевантное изображение
            image = self.create_relevant_image(signal['title'], "signal")
            post_text = self.format_signal_text(signal)

            success = await self.send_photo_message(image, post_text)

            if success:
                self.published_signals.add(signal['id'])
                self.save_published_news()
                logger.info(f"Успешно опубликован сигнал: {signal['ticker']}")
                return True
            else:
                logger.error(f"Ошибка публикации сигнала: {signal['ticker']}")
                return False

        except Exception as e:
            logger.error(f"Ошибка в публикации сигнала: {e}")
            return False

    async def get_bitcoinist_news(self):
        """Парсинг новостей с Bitcoinist"""
        try:
            url = "https://bitcoinist.com/"
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            }

            logger.info("Получаем новости с Bitcoinist...")
            async with self.session.get(url, headers=headers) as response:
                if response.status == 200:
                    html = await response.text()
                else:
                    return []

            soup = BeautifulSoup(html, 'html.parser')
            articles = []

            headlines = soup.find_all(['h2', 'h3'])[:8]

            for headline in headlines:
                try:
                    title_elem = headline.find('a')
                    if title_elem:
                        title = title_elem.text.strip()
                        link = title_elem.get('href', '')

                        if title and len(title) > 20:
                            translated_title = self.ai_translate_text(title)

                            if link and not link.startswith('http'):
                                link = 'https://bitcoinist.com' + link

                            news_id = hash(translated_title[:100])
                            if news_id not in self.published_news:
                                articles.append({
                                    'title': translated_title,
                                    'link': link,
                                    'source': 'Bitcoinist',
                                    'id': news_id
                                })
                except Exception:
                    continue

            logger.info(f"Найдено {len(articles)} новых новостей с Bitcoinist")
            return articles[:3]

        except Exception as e:
            logger.error(f"Error parsing Bitcoinist: {e}")
            return []

    async def get_coingecko_news(self):
        """Парсинг новостей с CoinGecko"""
        try:
            url = "https://www.coingecko.com/en/news"
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            }

            logger.info("Получаем новости с CoinGecko...")
            async with self.session.get(url, headers=headers) as response:
                if response.status == 200:
                    html = await response.text()
                else:
                    return []

            soup = BeautifulSoup(html, 'html.parser')
            articles = []

            news_items = soup.find_all('a', href=lambda x: x and '/news/' in x)[:6]

            for item in news_items:
                try:
                    title = item.text.strip()
                    if title and len(title) > 25:
                        translated_title = self.ai_translate_text(title)

                        link = item.get('href', '')
                        if link and not link.startswith('http'):
                            link = 'https://www.coingecko.com' + link

                        news_id = hash(translated_title[:100])
                        if news_id not in self.published_news:
                            articles.append({
                                'title': translated_title,
                                'link': link,
                                'source': 'CoinGecko',
                                'id': news_id
                            })
                except Exception:
                    continue

            return articles[:3]

        except Exception as e:
            logger.error(f"Error parsing CoinGecko: {e}")
            return []

    async def get_newsbtc_news(self):
        """Парсинг новостей с NewsBTC"""
        try:
            url = "https://www.newsbtc.com/"
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            }

            logger.info("Получаем новости с NewsBTC...")
            async with self.session.get(url, headers=headers) as response:
                if response.status == 200:
                    html = await response.text()
                else:
                    return []

            soup = BeautifulSoup(html, 'html.parser')
            articles = []

            headlines = soup.find_all(['h2', 'h3'])[:6]

            for headline in headlines:
                try:
                    title_elem = headline.find('a')
                    if title_elem:
                        title = title_elem.text.strip()
                        link = title_elem.get('href', '')

                        if title and len(title) > 20:
                            translated_title = self.ai_translate_text(title)

                            if link and not link.startswith('http'):
                                link = 'https://www.newsbtc.com' + link

                            news_id = hash(translated_title[:100])
                            if news_id not in self.published_news:
                                articles.append({
                                    'title': translated_title,
                                    'link': link,
                                    'source': 'NewsBTC',
                                    'id': news_id
                                })
                except Exception:
                    continue

            return articles[:3]

        except Exception as e:
            logger.error(f"Error parsing NewsBTC: {e}")
            return []

    async def get_real_news(self):
        """Получение реальных новостей со всех источников"""
        all_articles = []

        sources = [
            self.get_bitcoinist_news(),
            self.get_coingecko_news(),
            self.get_newsbtc_news()
        ]

        results = await asyncio.gather(*sources, return_exceptions=True)

        for result in results:
            if isinstance(result, list):
                all_articles.extend(result)

        # Если новостей нет, генерируем свои на русском
        if not all_articles:
            backup_news = [
                "Биткоин обновляет максимумы на фоне роста институционального спроса",
                "Эфириум демонстрирует уверенный рост перед крупным обновлением сети",
                "Рынок криптовалют показывает бычий тренд с увеличением объемов",
                "Крупные инвесторы увеличивают аллокацию в цифровые активы",
                "DeFi сектор продолжает привлекать миллиардные инвестиции",
                "Цена Bitcoin пробивает ключевой уровень сопротивления",
                "Ethereum готовится к масштабному обновлению Ethereum 2.0",
                "Рост волатильности создает новые возможности для трейдеров"
            ]
            for title in backup_news:
                all_articles.append({
                    'title': title,
                    'source': 'ANT CAPITAL',
                    'link': '',
                    'id': hash(title)
                })

        random.shuffle(all_articles)
        logger.info(f"Всего собрано {len(all_articles)} новостей")
        return all_articles[:5]

    def format_post_text(self, article):
        """Форматирование текста новости с AI переводом"""
        title = self.ai_translate_text(article['title'])
        source = article['source']
        link = article['link']

        emoji = random.choice(self.emojis)
        start_phrase = random.choice([
            f"{emoji} ВАЖНЕЙШАЯ ИНФА ПО ТРЕЙДУ!",
            f"{emoji} ХАЙПАНЕМ НА ЭТОЙ НОВОСТИ!",
            f"{emoji} ТО, ЧТО ВСЕ ЖДАЛИ!",
        ])

        post_text = f"<b>{start_phrase}</b>\n\n"
        post_text += f"{title}\n\n"

        reaction = random.choice([
            "💥 Это может изменить всё!",
            "🚀 Заряжаем ракеты!",
            "💎 Алмазные руки знают!",
            "🔥 Готовьте портфели к взлету!",
            "🎯 Идеальный момент для входа!"
        ])
        post_text += f"{reaction}\n\n"

        if link:
            post_text += f"<a href='{link}'>Читать подробнее</a>\n\n"

        post_text += "👍 Лайк если актуально! 🔔 Подписывайся!\n\n"

        # Хештеги
        post_text += "#Crypto #Трейдинг"
        if any(word in title.lower() for word in ['bitcoin', 'btc', 'биткоин']):
            post_text += " #Bitcoin #BTC"
        elif any(word in title.lower() for word in ['ethereum', 'eth', 'эфириум']):
            post_text += " #Ethereum #ETH"

        return post_text

    async def publish_news_round(self):
        """Один цикл публикации новостей с релевантными изображениями"""
        try:
            logger.info("Начинаем публикацию новостей...")

            fresh_news = await self.get_real_news()

            if not fresh_news:
                logger.warning("Новых новостей не найдено")
                return False

            article = random.choice(fresh_news)

            # Создаем релевантное изображение
            image = self.create_relevant_image(article['title'], "news")
            post_text = self.format_post_text(article)

            success = await self.send_photo_message(image, post_text)

            if success:
                self.published_news.add(article['id'])
                self.save_published_news()
                logger.info(f"Успешно опубликовано: {article['title']}")
                return True
            else:
                logger.error(f"Ошибка публикации: {article['title']}")
                return False

        except Exception as e:
            logger.error(f"Ошибка в цикле публикации: {e}")
            return False

    async def run(self):
        """Основной цикл бота"""
        await self.init_session()

        logger.info("ANT CAPITAL Crypto Bot Запущен!")
        logger.info(f"Канал: {self.channel}")

        # Приветственное сообщение
        welcome_msg = (
            "🚀 <b>ANT CAPITAL В ЭФИРЕ!</b>\n\n"
            "💎 Самый хайповый крипто-канал\n"
            "📈 Актуальные новости рынка\n"
            "🎯 Эксклюзивные крипто-сигналы\n"
            "⚡ Аналитика и инсайды\n\n"
            "🔔 ПОДПИСЫВАЙСЯ И ВКЛЮЧАЙ УВЕДОМЛЕНИЯ!\n\n"
            "#ANT_CAPITAL #Крипта #Сигналы #Трейдинг"
        )
        await self.send_message(welcome_msg)

        await asyncio.sleep(10)

        while True:
            try:
                # Чередуем новости и сигналы
                if random.random() < 0.6:  # 60% новостей, 40% сигналов
                    success = await self.publish_news_round()
                else:
                    success = await self.publish_signal()

                if success:
                    # Успешная публикация - случайная пауза
                    wait_time = random.randint(1800, 5400)  # 30-90 минут
                else:
                    # Если публикация не удалась - короче пауза
                    wait_time = random.randint(600, 1800)  # 10-30 минут

                logger.info(f"Следующая публикация через {wait_time // 60} минут")
                await asyncio.sleep(wait_time)

            except Exception as e:
                logger.error(f"Ошибка в основном цикле: {e}")
                await asyncio.sleep(300)  # 5 минут при ошибке

    async def send_message(self, text):
        """Отправка простого текстового сообщения"""
        url = f"https://api.telegram.org/bot{self.token}/sendMessage"
        data = {
            'chat_id': self.channel,
            'text': text,
            'parse_mode': 'HTML'
        }

        try:
            response = requests.post(url, data=data)
            if response.status_code == 200:
                logger.info("Сообщение отправлено успешно!")
                return True
            else:
                logger.error(f"Ошибка отправки: {response.text}")
                return False
        except Exception as e:
            logger.error(f"Ошибка: {e}")
            return False

    async def send_photo_message(self, image_buffer, caption):
        """Отправка сообщения с фото в Telegram"""
        try:
            url = f"https://api.telegram.org/bot{self.token}/sendPhoto"

            files = {
                'photo': ('content.jpg', image_buffer.getvalue(), 'image/jpeg')
            }

            data = {
                'chat_id': self.channel,
                'caption': caption,
                'parse_mode': 'HTML'
            }

            response = requests.post(url, files=files, data=data, timeout=30)

            if response.status_code == 200:
                logger.info("Контент отправлен успешно!")
                return True
            else:
                logger.error(f"Ошибка отправки: {response.text}")
                return False
        except Exception as e:
            logger.error(f"Error sending content: {e}")
            return False


async def main():
    bot = CryptoNewsBot()
    try:
        await bot.run()
    except KeyboardInterrupt:
        logger.info("Бот остановлен пользователем")
    finally:
        await bot.close_session()


if __name__ == "__main__":
    asyncio.run(main())