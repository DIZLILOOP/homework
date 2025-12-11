#!/usr/bin/env python3
"""
Инструмент командной строки для учебного конфигурационного языка.
Преобразует текст из входного формата в XML.
"""

import sys
import re
import json
from typing import List, Dict, Any
from xml.etree.ElementTree import Element, SubElement, tostring
from xml.dom import minidom

class ConfigParser:
    def __init__(self):
        self.constants = {}
        self.pos = 0
        self.line = 1
        self.column = 1
        self.text = ""
        
    def parse(self, input_text: str) -> str:
        """Основной метод парсинга"""
        self.text = input_text
        self.pos = 0
        self.line = 1
        self.column = 1
        self.constants = {}
        
        # Удаляем комментарии
        cleaned_text = self.remove_comments(input_text)
        
        # Парсим константы
        self.parse_constants(cleaned_text)
        
        # Создаем XML
        return self.generate_xml()
    
    def remove_comments(self, text: str) -> str:
        """Удаляет многострочные и однострочные комментарии"""
        # Удаляем многострочные комментарии #= ... =#
        lines = text.split('\n')
        result = []
        in_multiline = False
        
        for line in lines:
            i = 0
            cleaned_line = []
            line_len = len(line)
            
            while i < line_len:
                if not in_multiline and line[i] == '#':
                    if i + 1 < line_len and line[i + 1] == '=':
                        in_multiline = True
                        i += 2
                        continue
                    else:
                        # Однострочный комментарий
                        break
                elif in_multiline:
                    if i + 1 < line_len and line[i] == '=' and line[i + 1] == '#':
                        in_multiline = False
                        i += 2
                        continue
                    i += 1
                else:
                    cleaned_line.append(line[i])
                    i += 1
            
            if not in_multiline and cleaned_line:
                result.append(''.join(cleaned_line))
        
        return '\n'.join(result)
    
    def skip_whitespace(self, text: str) -> None:
        """Пропускает пробельные символы"""
        while self.pos < len(text) and text[self.pos] in ' \t\n\r':
            if text[self.pos] == '\n':
                self.line += 1
                self.column = 1
            else:
                self.column += 1
            self.pos += 1
    
    def parse_value(self, text: str) -> Any:
        """Парсит значение (число, массив или словарь)"""
        self.skip_whitespace(text)
        
        if self.pos >= len(text):
            raise SyntaxError(f"Ожидалось значение в строке {self.line}")
        
        # Строка (в кавычках)
        if text[self.pos] == '"':
            return self.parse_string(text)
        
        # Массив
        elif text.startswith('array(', self.pos):
            return self.parse_array(text)
        
        # Словарь
        elif text[self.pos] == '{':
            return self.parse_dict(text)
        
        # Булево значение
        elif text.startswith('true', self.pos):
            self.pos += 4
            self.column += 4
            return True
        elif text.startswith('false', self.pos):
            self.pos += 5
            self.column += 5
            return False
        
        # Число
        elif re.match(r'[+-]?\d', text[self.pos]):
            return self.parse_number(text)
        
        # Константа
        elif re.match(r'[A-Z_]', text[self.pos]):
            name = self.parse_name(text)
            if name in self.constants:
                return self.constants[name]
            raise NameError(f"Неизвестная константа: {name}")
        
        else:
            raise SyntaxError(f"Неизвестное значение в строке {self.line}: символ '{text[self.pos]}'")
    
    def parse_string(self, text: str) -> str:
        """Парсит строку в кавычках"""
        if text[self.pos] != '"':
            raise SyntaxError(f"Ожидалась строка в кавычках в строке {self.line}")
        
        self.pos += 1
        self.column += 1
        start = self.pos
        
        while self.pos < len(text) and text[self.pos] != '"':
            if text[self.pos] == '\n':
                raise SyntaxError(f"Незавершенная строка в строке {self.line}")
            self.pos += 1
            self.column += 1
        
        if self.pos >= len(text):
            raise SyntaxError(f"Незавершенная строка в строке {self.line}")
        
        string_value = text[start:self.pos]
        self.pos += 1  # Пропускаем закрывающую кавычку
        self.column += 1
        
        return string_value
    
    def parse_number(self, text: str) -> float:
        """Парсит число"""
        start = self.pos
        
        # Проверяем знак
        if text[self.pos] in '+-':
            self.pos += 1
        
        # Целая часть
        while self.pos < len(text) and text[self.pos].isdigit():
            self.pos += 1
        
        # Дробная часть
        if self.pos < len(text) and text[self.pos] == '.':
            self.pos += 1
            while self.pos < len(text) and text[self.pos].isdigit():
                self.pos += 1
        
        number_str = text[start:self.pos]
        
        # Проверяем, что это действительно число
        if '.' in number_str:
            try:
                value = float(number_str)
            except ValueError:
                raise SyntaxError(f"Неверный формат числа: {number_str}")
        else:
            try:
                value = int(number_str)
            except ValueError:
                raise SyntaxError(f"Неверный формат числа: {number_str}")
        
        self.column += (self.pos - start)
        return value
    
    def parse_array(self, text: str) -> List[Any]:
        """Парсит массив"""
        if not text.startswith('array(', self.pos):
            raise SyntaxError(f"Ожидалось 'array(' в строке {self.line}")
        
        self.pos += 6  # Пропускаем 'array('
        self.column += 6
        
        result = []
        
        while True:
            self.skip_whitespace(text)
            
            if self.pos >= len(text):
                raise SyntaxError(f"Незавершенный массив в строке {self.line}")
            
            # Проверяем конец массива
            if text[self.pos] == ')':
                self.pos += 1
                self.column += 1
                break
            
            # Парсим значение
            value = self.parse_value(text)
            result.append(value)
            
            self.skip_whitespace(text)
            
            # Проверяем разделитель или конец
            if self.pos < len(text) and text[self.pos] == ',':
                self.pos += 1
                self.column += 1
                continue
            elif text[self.pos] == ')':
                continue
            else:
                raise SyntaxError(f"Ожидалась ',' или ')' в строке {self.line}")
        
        return result
    
    def parse_dict(self, text: str) -> Dict[str, Any]:
        """Парсит словарь"""
        if text[self.pos] != '{':
            raise SyntaxError(f"Ожидалось '{{' в строке {self.line}")
        
        self.pos += 1
        self.column += 1
        
        result = {}
        
        while True:
            self.skip_whitespace(text)
            
            if self.pos >= len(text):
                raise SyntaxError(f"Незавершенный словарь в строке {self.line}")
            
            # Проверяем конец словаря
            if text[self.pos] == '}':
                self.pos += 1
                self.column += 1
                break
            
            # Парсим имя
            if not re.match(r'[A-Z_]', text[self.pos]):
                raise SyntaxError(f"Ожидалось имя [A-Z_] в строке {self.line}")
            
            name = self.parse_name(text)
            
            self.skip_whitespace(text)
            
            # Проверяем двоеточие
            if self.pos >= len(text) or text[self.pos] != ':':
                raise SyntaxError(f"Ожидалось ':' после имени {name} в строке {self.line}")
            
            self.pos += 1
            self.column += 1
            
            # Парсим значение
            value = self.parse_value(text)
            result[name] = value
            
            self.skip_whitespace(text)
            
            # Проверяем разделитель или конец
            if self.pos < len(text) and text[self.pos] == ',':
                self.pos += 1
                self.column += 1
                continue
            elif text[self.pos] == '}':
                continue
            else:
                raise SyntaxError(f"Ожидалась ',' или '}}' в строке {self.line}")
        
        return result
    
    def parse_name(self, text: str) -> str:
        """Парсит имя (идентификатор)"""
        start = self.pos
        while self.pos < len(text) and (text[self.pos].isupper() or text[self.pos] == '_'):
            self.pos += 1
        
        name = text[start:self.pos]
        
        if not name:
            raise SyntaxError(f"Пустое имя в строке {self.line}")
        
        self.column += (self.pos - start)
        return name
    
    def parse_constants(self, text: str) -> None:
        """Парсит объявления констант"""
        self.pos = 0
        self.line = 1
        self.column = 1
        
        while self.pos < len(text):
            self.skip_whitespace(text)
            
            if self.pos >= len(text):
                break
            
            # Ищем const
            if text.startswith('const', self.pos):
                self.pos += 5
                self.column += 5
                
                self.skip_whitespace(text)
                
                # Парсим имя
                name = self.parse_name(text)
                
                self.skip_whitespace(text)
                
                # Проверяем =
                if self.pos >= len(text) or text[self.pos] != '=':
                    raise SyntaxError(f"Ожидалось '=' после const {name}")
                
                self.pos += 1
                self.column += 1
                
                # Парсим значение
                value = self.parse_value(text)
                self.constants[name] = value
                
                self.skip_whitespace(text)
                
                # Точка с запятой не обязательна, пропускаем если есть
                if self.pos < len(text) and text[self.pos] == ';':
                    self.pos += 1
                    self.column += 1
            else:
                # Если не нашли const, просто пропускаем символ
                # (на случай если остались пробелы или пустые строки)
                self.pos += 1
                self.column += 1
    
    def generate_xml(self) -> str:
        """Генерирует XML из распарсенных данных"""
        root = Element('configuration')
        
        for name, value in self.constants.items():
            const_elem = SubElement(root, 'constant')
            const_elem.set('name', name)
            
            # Определяем тип и сохраняем значение
            if isinstance(value, dict):
                const_elem.set('type', 'dict')
                # Преобразуем словарь в JSON строку
                const_elem.text = json.dumps(value, ensure_ascii=False)
            elif isinstance(value, list):
                const_elem.set('type', 'array')
                # Преобразуем массив в JSON строку
                const_elem.text = json.dumps(value, ensure_ascii=False)
            elif isinstance(value, bool):
                const_elem.set('type', 'boolean')
                const_elem.text = str(value).lower()
            elif isinstance(value, (int, float)):
                const_elem.set('type', 'number')
                const_elem.text = str(value)
            else:
                const_elem.set('type', 'string')
                const_elem.text = str(value)
        
        # Форматируем XML
        xml_str = tostring(root, encoding='unicode')
        dom = minidom.parseString(xml_str)
        return dom.toprettyxml(indent="  ")

def main():
    """Основная функция командной строки"""
    if len(sys.argv) > 1:
        # Чтение из файла с автоматическим определением кодировки
        filename = sys.argv[1]
        try:
            # Пробуем UTF-8
            with open(filename, 'r', encoding='utf-8') as f:
                input_text = f.read()
        except UnicodeDecodeError:
            try:
                # Пробуем UTF-8 с BOM
                with open(filename, 'r', encoding='utf-8-sig') as f:
                    input_text = f.read()
            except UnicodeDecodeError:
                try:
                    # Пробуем UTF-16
                    with open(filename, 'r', encoding='utf-16') as f:
                        input_text = f.read()
                except UnicodeDecodeError:
                    # Пробуем Windows-1251 (русская кодировка)
                    with open(filename, 'r', encoding='windows-1251') as f:
                        input_text = f.read()
    else:
        # Чтение из stdin
        input_text = sys.stdin.read()
    
    try:
        parser = ConfigParser()
        xml_output = parser.parse(input_text)
        
        # Выводим результат
        print(xml_output)
        
    except SyntaxError as e:
        print(f"Синтаксическая ошибка: {e}", file=sys.stderr)
        sys.exit(1)
    except NameError as e:
        print(f"Ошибка имени: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Ошибка: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()