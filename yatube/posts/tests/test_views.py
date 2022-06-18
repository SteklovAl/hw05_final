from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from django import forms
from django.core.files.uploadedfile import SimpleUploadedFile
from posts.models import Post, Group, Follow
from django.core.cache import cache


User = get_user_model()
ALL_POST_NUMBER = 15
FIRST_POST_NUMBER = 10
SECOND_POST_NUMBER = ALL_POST_NUMBER - FIRST_POST_NUMBER


class PostsURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='author')
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            group=cls.group,
            text='Тестовый пост для проверки',
            image=uploaded,
        )
        cls.guest_client = Client()
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)

    def tearDown(self):
        cache.clear()

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_pages_names = {
            reverse('posts:index'): 'posts/index.html',
            reverse('posts:profile', kwargs={'username': self.user}):
                'posts/profile.html',
            reverse('posts:post_detail', kwargs={'post_id': self.post.pk}):
                'posts/post_detail.html',
            reverse('posts:post_create'): 'posts/create_post.html',
            reverse('posts:group_list', kwargs={'slug': self.group.slug}):
                'posts/group_list.html',
            reverse('posts:post_edit', kwargs={'post_id': self.post.pk}):
                'posts/create_post.html'
        }
        for template, reverse_name in templates_pages_names.items():
            with self.subTest(template=template):
                response = self.authorized_client.get(template)
                self.assertTemplateUsed(response, reverse_name)

    def test_pages_show_correct_context(self):
        """Шаблоны index, profile, group_list"""
        """сформированы с правильным контекстом."""
        cache.clear()
        templates = [
            reverse('posts:index'),
            reverse('posts:profile', kwargs={'username': self.user}),
            reverse('posts:group_list', kwargs={'slug': self.group.slug}),
        ]
        for template in templates:
            with self.subTest(template=template):
                response = self.authorized_client.get(template)
                first_object = response.context['page_obj'][0]
                self.assertEqual(first_object.text, self.post.text)
                self.assertEqual(first_object.author, self.user)
                self.assertEqual(first_object.group, self.group)
                self.assertTrue(first_object.image, self.post.image)

    def test_post_detail_pages_show_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:post_detail', kwargs={'post_id': self.post.pk})
        )
        post = response.context['post']
        self.assertEqual(post.text, self.post.text)
        self.assertEqual(post.author, self.user)
        self.assertEqual(post.group, self.group)
        self.assertTrue(post.image, self.post.image)

    def test_post_create_show_correct_context(self):
        """Шаблон post_create сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:post_create'))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }

        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_post_edit_show_correct_context(self):
        """Шаблон post_create сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:post_edit', kwargs={'post_id': self.post.pk})
        )
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }

        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='author')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_slug',
            description='Тестовое описание',
        )
        cls.authorized_client = Client()

    def setUp(self):
        for post in range(ALL_POST_NUMBER):
            Post.objects.create(
                text=f'text{post}',
                author=self.user,
                group=self.group,
            )

    def tearDown(self):
        cache.clear()

    def test_first_page(self):
        """На первой странице 10 записей"""
        cache.clear()
        templates_pages_names = {
            'posts/index.html': reverse('posts:index'),
            'posts/profile.html':
                reverse('posts:profile', kwargs={'username': self.user}),
            'posts/group_list.html':
                reverse('posts:group_list', kwargs={'slug': self.group.slug}),
        }
        for template, reverse_name in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertEqual(
                    len(response.context['page_obj']), FIRST_POST_NUMBER
                )

    def test_second_page(self):
        """На вторй странице 5 записей"""
        templates_pages_names = {
            'posts/index.html': reverse('posts:index'),
            'posts/profile.html':
                reverse('posts:profile', kwargs={'username': self.user}),
            'posts/group_list.html':
                reverse('posts:group_list', kwargs={'slug': self.group.slug}),
        }
        for template, reverse_name in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name + '?page=2')
                self.assertEqual(
                    len(response.context['page_obj']), SECOND_POST_NUMBER
                )


class FollowTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user_1 = User.objects.create_user(username='Подписчик')
        cls.user_2 = User.objects.create_user(username='Автор')
        cls.post = Post.objects.create(
            text='Тестовый текст',
            author=cls.user_2,
        )

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user_1)

    def test_follow(self):
        """Авторизованный пользователь может подписываться"""
        self.authorized_client.get(
            reverse('posts:profile_follow', kwargs={'username': self.user_2})
        )
        self.assertTrue(
            Follow.objects.filter(
                user=self.user_1,
                author=self.user_2,
            ).exists())

    def test_unfollow(self):
        """Авторизованный пользователь может отписываться"""
        self.authorized_client.get(
            reverse('posts:profile_follow', kwargs={'username': self.user_2})
        )
        self.authorized_client.get(
            reverse(
                'posts:profile_unfollow', kwargs={'username': self.user_2})
        )
        self.assertFalse(
            Follow.objects.filter(
                user=self.user_1,
                author=self.user_2,
            ).exists())

    def test_follow_index(self):
        """Новая запись пользователя появляется в ленте подписчиков"""
        self.authorized_client.get(
            reverse('posts:profile_follow', kwargs={'username': self.user_2})
        )
        response = self.authorized_client.get(reverse('posts:follow_index'))
        self.assertEqual(response.context.get('page_obj')[0], self.post)
