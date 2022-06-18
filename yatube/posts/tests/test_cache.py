from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from posts.models import Post, Group
from django.core.cache import cache
from django.urls import reverse


User = get_user_model()


class PostsCacheTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='author')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            text='Тестовый текст',
            author=cls.user,
            group=cls.group
        )

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_cache_index(self):
        """Проверка кеширования главной страницы"""
        response = self.authorized_client.get(reverse('posts:index'))
        content = response.content
        Post.objects.create(
            text='test_new_post',
            author=self.user,
        )
        response_old = self.authorized_client.get(reverse('posts:index'))
        old_content = response_old.content
        self.assertEqual(old_content, content)
        cache.clear()
        response_new = self.authorized_client.get(reverse('posts:index'))
        new_content = response_new.content
        self.assertNotEqual(old_content, new_content)
