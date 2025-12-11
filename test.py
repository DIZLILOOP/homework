#!/usr/bin/env python3
"""Тестирование парсера"""

from config_parser import ConfigParser

def test_example1():
    """Тест первого примера"""
    with open('example1.config', 'r', encoding='utf-8') as f:
        text = f.read()
    
    parser = ConfigParser()
    result = parser.parse(text)
    
    print("=" * 60)
    print("Тест 1 пройден!")
    print("=" * 60)
    print(result)
    print("=" * 60)

def test_example2():
    """Тест второго примера"""
    with open('example2.config', 'r', encoding='utf-8') as f:
        text = f.read()
    
    parser = ConfigParser()
    result = parser.parse(text)
    
    print("\n" + "=" * 60)
    print("Тест 2 пройден!")
    print("=" * 60)
    print(result)
    print("=" * 60)

def test_example3():
    """Тест третьего примера"""
    with open('example3.config', 'r', encoding='utf-8') as f:
        text = f.read()
    
    parser = ConfigParser()
    result = parser.parse(text)
    
    print("\n" + "=" * 60)
    print("Тест 3 пройден!")
    print("=" * 60)
    print(result)
    print("=" * 60)

if __name__ == "__main__":
    try:
        test_example1()
        test_example2()
        test_example3()
        print("\n✅ Все тесты выполнены успешно!")
    except Exception as e:
        print(f"\n❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()