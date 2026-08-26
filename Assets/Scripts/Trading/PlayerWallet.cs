using System;

namespace FantasySurvival.Trading
{
    public enum TradeCurrency
    {
        Gold = 1,
        Silver = 2
    }

    /// <summary>
    /// Authoritative runtime balance owned by one PlayerInventoryState.
    /// Merchant stock deliberately has no wallet; this class is Player-only.
    /// </summary>
    public sealed class PlayerWallet
    {
        public const int StartingGold = 5000;
        public const int StartingSilver = 5000;

        public event Action Changed;

        public int Gold { get; private set; }
        public int Silver { get; private set; }

        public PlayerWallet()
            : this(StartingGold, StartingSilver)
        {
        }

        public PlayerWallet(int gold, int silver)
        {
            if (gold < 0 || silver < 0)
            {
                throw new ArgumentOutOfRangeException(
                    nameof(gold),
                    "Currency balances cannot be negative.");
            }

            Gold = gold;
            Silver = silver;
        }

        public int GetBalance(TradeCurrency currency)
        {
            switch (currency)
            {
                case TradeCurrency.Gold: return Gold;
                case TradeCurrency.Silver: return Silver;
                default: return 0;
            }
        }

        public bool CanSpend(TradeCurrency currency, int amount)
        {
            return amount >= 0 && IsValidCurrency(currency) && GetBalance(currency) >= amount;
        }

        public bool TrySpend(TradeCurrency currency, int amount)
        {
            if (!CanSpend(currency, amount))
            {
                return false;
            }

            if (amount == 0)
            {
                return true;
            }

            if (currency == TradeCurrency.Gold)
            {
                Gold -= amount;
            }
            else
            {
                Silver -= amount;
            }

            Changed?.Invoke();
            return true;
        }

        public bool CanCredit(TradeCurrency currency, int amount)
        {
            if (amount < 0 || !IsValidCurrency(currency))
            {
                return false;
            }

            return GetBalance(currency) <= int.MaxValue - amount;
        }

        public bool TryCredit(TradeCurrency currency, int amount)
        {
            if (!CanCredit(currency, amount))
            {
                return false;
            }

            if (amount == 0)
            {
                return true;
            }

            if (currency == TradeCurrency.Gold)
            {
                Gold += amount;
            }
            else
            {
                Silver += amount;
            }

            Changed?.Invoke();
            return true;
        }

        public static bool IsValidCurrency(TradeCurrency currency)
        {
            return currency == TradeCurrency.Gold || currency == TradeCurrency.Silver;
        }
    }
}
