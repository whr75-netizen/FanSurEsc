using FantasySurvival.Trading;

namespace FantasySurvival.SaveSystem
{
    public static class PlayerCurrencySaveCodec
    {
        public static PlayerCurrencySaveData CreateStartingSaveData()
        {
            return new PlayerCurrencySaveData
            {
                formatVersion = PlayerCurrencySaveData.CurrentFormatVersion,
                gold = PlayerWallet.StartingGold,
                silver = PlayerWallet.StartingSilver
            };
        }

        public static bool TryCapture(
            PlayerWallet wallet,
            out PlayerCurrencySaveData saveData,
            out string error)
        {
            saveData = null;
            if (wallet == null)
            {
                error = "Player wallet is missing.";
                return false;
            }

            saveData = new PlayerCurrencySaveData
            {
                formatVersion = PlayerCurrencySaveData.CurrentFormatVersion,
                gold = wallet.Gold,
                silver = wallet.Silver
            };
            error = null;
            return true;
        }

        public static bool TryRestore(
            PlayerCurrencySaveData saveData,
            out PlayerWallet wallet,
            out string error)
        {
            wallet = null;
            if (saveData == null ||
                saveData.formatVersion != PlayerCurrencySaveData.CurrentFormatVersion)
            {
                error = "Player currency payload is missing or has an unsupported version.";
                return false;
            }

            if (saveData.gold < 0 || saveData.silver < 0)
            {
                error = "Player currency payload contains a negative balance.";
                return false;
            }

            wallet = new PlayerWallet(saveData.gold, saveData.silver);
            error = null;
            return true;
        }
    }
}
