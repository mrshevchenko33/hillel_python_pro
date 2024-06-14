import multiprocessing as mp
import time

def sum_lucky_tickets(ticket):
    ticket_str = str(ticket).zfill(8)
    sum_half_first = sum(int(digit) for digit in ticket_str[:4])
    sum_half_second = sum(int(digit) for digit in ticket_str[4:])
    return sum_half_first == sum_half_second

def get_count(start, end, res):
    count = 0
    for ticket in range(start, end):
        if sum_lucky_tickets(ticket):
            count += 1
    res.put(count)

def main():
    start = time.time()
    queues = []
    processes = []

    ranges = [
        (1, 6_250_001),
        (6_250_001, 12_500_001),
        (12_500_001, 18_750_001),
        (18_750_001, 25_000_001),
        (25_000_001, 31_250_001),
        (31_250_001, 37_500_001),
        (37_500_001, 43_750_001),
        (43_750_001, 50_000_001),
        (50_000_001, 56_250_001),
        (56_250_001, 62_500_001),
        (62_500_001, 68_750_001),
        (68_750_001, 75_000_001),
        (75_000_001, 81_250_001),
        (81_250_001, 87_500_001),
        (87_500_001, 93_750_001),
        (93_750_001, 100_000_001)
    ]

    for i in range(16):
        q = mp.Queue()
        queues.append(q)
        p = mp.Process(target=get_count, args=(ranges[i][0], ranges[i][1], q))
        processes.append(p)
        p.start()

    for p in processes:
        p.join()

    total_count = sum(q.get() for q in queues)
    end = time.time()
    print(f'Щасливих квитків: {total_count}, time: {end - start}')

if __name__ == '__main__':
    main()
