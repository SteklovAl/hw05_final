from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from django.core.cache import cache
from posts.models import Post, Group

User = get_user_model()


class StaticURLTests(TestCase):
    def test_homepage(self):
        guest_client = Client()
        response = guest_client.get('/')
        self.assertEqual(response.status_code, 200)


class PostsURLTests(TestCase):
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
            author=cls.user,
            group=cls.group,
            text='Тестовый пост для проверки',
        )

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        cache.clear()

    def test_home_url_exists_at_desired_location(self):
        """Страница / доступна любому пользователю."""
        cache.clear()
        response = self.guest_client.get('/')
        self.assertEqual(response.status_code, 200)

    def test_profile_url_exists_at_desired_location(self):
        """Страница profile/<str:username>/ доступна любому пользователю."""
        response = self.guest_client.get('/profile/author/')
        self.assertEqual(response.status_code, 200)

    def test_group_exists_at_desired_location(self):
        """Страница group/<slug>/ доступна любому пользователю."""
        response = self.guest_client.get('/group/test_slug/')
        self.assertEqual(response.status_code, 200)

    def test_post_detail_url_exists_at_desired_location(self):
        """Страница posts/<post_id>/ доступна авторизованному пользователю."""
        response = self.guest_client.get('/posts/1/')
        self.assertEqual(response.status_code, 200)

    def test_unexisting_page_exists_at_desired_location(self):
        """Несуществующая страница не доступна."""
        response = self.guest_client.get('/wrfrt/')
        self.assertEqual(response.status_code, 404)

    def test_create_url_exists_at_desired_location(self):
        """Страница create/ доступна авторизованному пользователю."""
        response = self.authorized_client.get('/create/')
        self.assertEqual(response.status_code, 200)

    def test_post_edit_url_exists_at_desired_location_authorized(self):
        """Страница posts/<int:post_id>/edit/ доступна автору."""
        response = self.authorized_client.get('/posts/1/edit/')
        self.assertEqual(response.status_code, 200)

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_url_names = {
            '/': 'posts/index.html',
            '/profile/author/': 'posts/profile.html',
            '/posts/1/': 'posts/post_detail.html',
            '/create/': 'posts/create_post.html',
            '/group/test_slug/': 'posts/group_list.html',
            '/posts/1/edit/': 'posts/create_post.html'
        }
        for template, url in templates_url_names.items():
            with self.subTest(template=template):
                response = self.authorized_client.get(template)
                self.assertTemplateUsed(response, url)
