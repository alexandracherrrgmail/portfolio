#!/usr/bin/env python3
import json
import os
import sys
from collections import Counter
from datetime import datetime
import requests

PROFESSIONS = [
    "Python",
    "Java",
    "Data Scientist",
    "Аналитик данных",
    "DevOps",
    "Frontend",
    "Product Manager",
    "Менеджер проектов",
    "HR менеджер",
    "Маркетолог",
]

REGION_ID = 113
VACANCIES_PER_PROFESSION = 100
SALARY_STATS_LIMIT = 50
TOP_SKILLS_LIMIT = 15

def fetch_vacancies(profession, region=REGION_ID, per_page=VACANCIES_PER_PROFESSION):
    url = "https://api.hh.ru/vacancies"
    params = {
        "text": profession,
        "area": region,
        "per_page": per_page,
        "only_with_salary": False,
    }
    try:
        response = requests.get(url, params=params, timeout=30)
        print(f"  → Статус ответа: {response.status_code}", file=sys.stderr)
        if response.status_code != 200:
            print(f"  → Ошибка: {response.text[:200]}", file=sys.stderr)
            return []
        data = response.json()
        found = data.get("found", 0)
        items = data.get("items", [])
        print(f"  → Найдено вакансий: {found}, загружено: {len(items)}", file=sys.stderr)
        return items
    except Exception as e:
        print(f"  → Исключение: {e}", file=sys.stderr)
        return []

def extract_salary(vacancy):
    salary = vacancy.get("salary")
    if not salary:
        return None
    currency = salary.get("currency", "RUR")
    if currency != "RUR":
        return None
    salary_from = salary.get("from")
    salary_to = salary.get("to")
    if salary_from and salary_to:
        return (salary_from + salary_to) / 2
    elif salary_from:
        return salary_from
    elif salary_to:
        return salary_to
    return None

def extract_skills(vacancy):
    skills = vacancy.get("key_skills", [])
    return [skill.get("name", "").lower().strip() for skill in skills if skill.get("name")]

def analyze_profession(profession):
    print(f"Анализирую: {profession}...", file=sys.stderr)
    vacancies = fetch_vacancies(profession)
    if not vacancies:
        return {
            "profession": profession,
            "vacancies_count": 0,
            "average_salary": None,
            "median_salary": None,
            "top_skills": [],
            "error": "Нет данных",
        }
    salaries = []
    for vac in vacancies[:SALARY_STATS_LIMIT]:
        sal = extract_salary(vac)
        if sal:
            salaries.append(sal)
    avg_salary = round(sum(salaries) / len(salaries)) if salaries else None
    sorted_salaries = sorted(salaries)
    median_salary = sorted_salaries[len(sorted_salaries)//2] if sorted_salaries else None
    all_skills = []
    for vac in vacancies:
        all_skills.extend(extract_skills(vac))
    skill_counter = Counter(all_skills)
    top_skills = [{"skill": skill, "count": count} for skill, count in skill_counter.most_common(TOP_SKILLS_LIMIT)]
    return {
        "profession": profession,
        "vacancies_count": len(vacancies),
        "average_salary": avg_salary,
        "median_salary": median_salary,
        "top_skills": top_skills,
    }

def main():
    print(f"=== Сбор трендов hh.ru === {datetime.now().isoformat()}", file=sys.stderr)
    results = []
    for prof in PROFESSIONS:
        results.append(analyze_profession(prof))
    output = {
        "last_updated": datetime.now().isoformat(),
        "region_id": REGION_ID,
        "professions": results,
    }
    os.makedirs("data", exist_ok=True)
    with open("data/trends.json", "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    print("✅ Готово! Файл сохранён в data/trends.json", file=sys.stderr)

if __name__ == "__main__":
    main()
