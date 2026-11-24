from django.db import connections
from django.db.migrations.executor import MigrationExecutor
from django.test import TransactionTestCase
from django.utils import timezone


class RevisionUserMigrationTest(TransactionTestCase):
    databases = {"default", "postgres"}

    def testIntegerUserMigrationPreservesHistory(self):
        for alias in self.databases:
            with self.subTest(database=alias):
                executor = MigrationExecutor(connections[alias])
                original_targets = executor.loader.graph.leaf_nodes()
                try:
                    other_targets = [node for node in original_targets if node[0] != "reversion"]
                    before = other_targets + [("reversion", "0002_add_index_on_version_for_content_type_and_db")]
                    executor.migrate(before)
                    apps = executor.loader.project_state(before).apps
                    user = apps.get_model("auth", "User").objects.using(alias).create(username="migration-author")
                    revision = apps.get_model("reversion", "Revision").objects.using(alias).create(
                        user_id=user.pk, date_created=timezone.now(), comment="historical comment",
                    )
                    anonymous = apps.get_model("reversion", "Revision").objects.using(alias).create(
                        date_created=timezone.now(), comment="anonymous revision",
                    )
                    content_type = apps.get_model("contenttypes", "ContentType").objects.using(alias).create(
                        app_label="test_app", model="historical",
                    )
                    version = apps.get_model("reversion", "Version").objects.using(alias).create(
                        revision_id=revision.pk, content_type_id=content_type.pk,
                        object_id="42", object_repr="historical", format="json", db=alias,
                        serialized_data="[]",
                    )
                    after = other_targets + [("reversion", "0003_alter_revision_user")]
                    executor = MigrationExecutor(connections[alias])
                    executor.migrate(after)
                    apps = executor.loader.project_state(after).apps
                    Revision = apps.get_model("reversion", "Revision")
                    self.assertFalse(Revision._meta.get_field("user").is_relation)
                    saved = Revision.objects.using(alias).get(pk=revision.pk)
                    self.assertEqual(saved.user, user.pk)
                    self.assertEqual(saved.date_created, revision.date_created)
                    self.assertEqual(saved.comment, revision.comment)
                    self.assertIsNone(Revision.objects.using(alias).get(pk=anonymous.pk).user)
                    saved_version = apps.get_model("reversion", "Version").objects.using(alias).get(pk=version.pk)
                    self.assertEqual(saved_version.serialized_data, version.serialized_data)
                    self.assertEqual(saved_version.revision_id, revision.pk)
                    apps.get_model("auth", "User").objects.using(alias).get(pk=user.pk).delete(using=alias)
                    self.assertEqual(Revision.objects.using(alias).get(pk=revision.pk).user, saved.user)
                finally:
                    MigrationExecutor(connections[alias]).migrate(original_targets)
