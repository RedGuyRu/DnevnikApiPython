class Utils:
    @staticmethod
    def average(numbers):
        return sum(numbers) / len(numbers)

    @staticmethod
    def parse_marks_with_weight(marks):
        parsed = []
        for mark in marks:
            if mark["weight"] == 0:
                continue
            parsed.append(mark["mark"] * mark["weight"])
        return parsed
