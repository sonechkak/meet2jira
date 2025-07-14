import asyncio
import bcrypt
from sqlalchemy import select

from src.database import create_db_and_tables, AsyncSessionLocal
from src.models.user import User


async def debug_authentication():
    """Отладка системы аутентификации"""
    print("🔍 Debugging authentication system...")

    await create_db_and_tables()

    async with AsyncSessionLocal() as session:
        try:
            # 1. Проверяем всех пользователей
            print("\n1️⃣ Checking all users in database:")
            result = await session.scalars(select(User))
            users = result.all()

            if not users:
                print("❌ No users found in database!")
                print("💡 Create a superuser first using create_superuser.py")
                return

            for user in users:
                print(
                    f"   👤 {user.username} | Email: {user.email or 'None'} | Superuser: {user.is_superuser} | Active: {user.is_active}")

            # 2. Проверяем суперпользователей
            print("\n2️⃣ Checking superusers:")
            superusers = await session.scalars(
                select(User).filter_by(is_superuser=True, is_active=True)
            )
            superuser_list = superusers.all()

            if not superuser_list:
                print("❌ No active superusers found!")
                print("💡 You need at least one active superuser to access admin")
                return

            # 3. Тестируем аутентификацию
            print("\n3️⃣ Testing authentication:")
            test_user = superuser_list[0]

            # Запрашиваем пароль для тестирования
            test_password = input(f"Enter password for '{test_user.username}' to test: ")

            # Проверяем пароль
            password_valid = bcrypt.checkpw(test_password.encode(), test_user.hashed_password.encode())
            print(f"🔑 Password validation: {'✅ Valid' if password_valid else '❌ Invalid'}")

            if password_valid:
                print(f"✅ Authentication should work for user: {test_user.username}")
            else:
                print(f"❌ Password incorrect for user: {test_user.username}")

            # 4. Показываем хеш пароля для отладки
            print(f"\n4️⃣ Password hash info:")
            print(f"   Hash: {test_user.hashed_password[:50]}...")
            print(f"   Hash length: {len(test_user.hashed_password)}")
            print(f"   Starts with $2b$: {test_user.hashed_password.startswith('$2b$')}")

        except Exception as e:
            print(f"❌ Error during debug: {e}")
            import traceback
            traceback.print_exc()


async def create_test_superuser():
    """Создание тестового суперпользователя"""
    print("🔧 Creating test superuser...")

    await create_db_and_tables()

    username = "admin1"
    password = "admin12345"
    email = "admin@example.comm"

    # Хешируем пароль
    hash_password = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

    async with AsyncSessionLocal() as session:
        try:
            # Проверяем что пользователь не существует
            existing = await session.scalars(
                select(User).filter_by(username=username)
            )
            if existing.first():
                print(f"❌ User '{username}' already exists!")
                return

            # Создаем пользователя
            user = User(
                username=username,
                email=email,
                hash_password=hash_password,
                is_superuser=True,
                is_active=True
            )

            session.add(user)
            await session.commit()

            print(f"✅ Test superuser created:")
            print(f"   Username: {username}")
            print(f"   Password: {password}")
            print(f"   Email: {email}")
            print(f"   ID: {user.id}")

        except Exception as e:
            print(f"❌ Error creating test user: {e}")
            await session.rollback()


async def test_fastadmin_auth():
    """Тестирование метода аутентификации FastAdmin"""
    print("🧪 Testing FastAdmin authentication method...")

    from src.admin.admin import UserAdmin

    # Создаем экземпляр админки
    admin = UserAdmin()

    # Запрашиваем данные для тестирования
    username = input("Username: ")
    password = input("Password: ")

    try:
        # Тестируем метод authenticate
        result = await admin.authenticate(username, password)

        if result:
            print(f"✅ Authentication successful! User ID: {result}")
        else:
            print("❌ Authentication failed!")

    except Exception as e:
        print(f"❌ Error in authenticate method: {e}")
        import traceback
        traceback.print_exc()


async def main():
    """Главная функция отладки"""
    print("🎯 FastAdmin Authentication Debugger")
    print("=" * 50)

    while True:
        print("\nOptions:")
        print("1. Debug authentication system")
        print("2. Create test superuser (admin/admin123)")
        print("3. Test FastAdmin authentication method")
        print("4. Exit")

        choice = input("\nSelect option (1-4): ").strip()

        if choice == "1":
            await debug_authentication()
        elif choice == "2":
            await create_test_superuser()
        elif choice == "3":
            await test_fastadmin_auth()
        elif choice == "4":
            print("👋 Goodbye!")
            break
        else:
            print("❌ Invalid option. Please select 1-4.")


if __name__ == "__main__":
    asyncio.run(main())