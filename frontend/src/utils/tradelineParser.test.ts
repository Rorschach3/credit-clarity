import { parseTradelinesFromText } from './tradelineParser';

describe('parseTradelinesFromText', () => {
  it('parses a valid open account tradeline correctly', () => {
    const input = `CHASE CARD
Account Number: 1234
Status: open account
Balance: $1000
Date Opened: 01/01/2020`;

    const { valid, rejected } = parseTradelinesFromText(input);
    expect(rejected).toHaveLength(0);
    expect(valid).toHaveLength(1);
    const t = valid[0];
    expect(t.creditorName).toBe('CHASE CARD');
    expect(t.accountNumber).toBe('1234');
    expect(t.accountStatus).toBe('open');
    expect(t.isNegative).toBe(false);
    expect(t.accountBalance).toBe('1000');
    expect(t.dateOpened).toBe('01/01/2020');
  });

  it('identifies a charged off tradeline as negative', () => {
    const input = `CHASE CARD
Account Number: 1234
Status: charged off
Balance: $0
Date Opened: 01/01/2020`;

    const { valid, rejected } = parseTradelinesFromText(input);
    expect(rejected).toHaveLength(0);
    expect(valid).toHaveLength(1);
    const t = valid[0];
    expect(t.accountStatus).toBe('chargedOff');
    expect(t.isNegative).toBe(true);
    expect(t.negativeReason).toMatch(/charged off/i);
  });

  it('rejects invalid tradeline entries', () => {
    const input = `Invalid Tradeline`;

    const { valid, rejected } = parseTradelinesFromText(input);
    expect(valid).toHaveLength(0);
    expect(rejected).toHaveLength(1);
    expect(rejected[0].entry).toBe('Invalid Tradeline');
    expect(rejected[0].errors.length).toBeGreaterThan(0);
  });
});
