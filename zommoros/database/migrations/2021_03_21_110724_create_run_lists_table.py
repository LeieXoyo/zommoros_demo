from orator.migrations import Migration


class CreateRunListsTable(Migration):

    def up(self):
        """
        Run the migrations.
        """
        with self.schema.create('run_lists') as table:
            table.increments('id')
            table.string('dataname')
            table.string('datetime')
            table.string('type')
            table.long_text('snapshot')
            table.string('starting_value').nullable()
            table.long_text('error').nullable()
            table.timestamps()

    def down(self):
        """
        Revert the migrations.
        """
        self.schema.drop('run_lists')
