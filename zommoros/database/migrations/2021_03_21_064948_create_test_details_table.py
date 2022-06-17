from orator.migrations import Migration


class CreateTestDetailsTable(Migration):

    def up(self):
        """
        Run the migrations.
        """
        with self.schema.create('test_details') as table:
            table.increments('id')
            table.integer('test_info_id')
            table.string('datetime')
            table.string('symbol')
            table.string('side')
            table.string('price')
            table.string('size')
            table.string('cost')
            table.string('fee')
            table.string('margin')
            table.string('cash')
            table.string('value')
            table.timestamps()

    def down(self):
        """
        Revert the migrations.
        """
        self.schema.drop('test_details')
